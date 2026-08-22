# Catalog Domain — Remodel

Replaces the current flat `Product` (single SKU/price/image, single category) with a variant-based model: every product is sold through one or more variants, which is where SKU, price, images, and attributes actually live.

---

## 1. Why

- A single `Product.sku`/`sell_price` can't represent "this t-shirt in Red/M and Blue/L are different SKUs at possibly different prices."
- `Product.category_id` (single FK) can't represent a product listed under more than one category.
- `is_active: bool` can't represent draft/in-review products, or distinguish "temporarily hidden" from "discontinued" — both currently collapse to `False` with no way to tell them apart later.

---

## 2. Entities

### Product
The conceptual item — not directly sellable, not directly priced.

| Field | Type | Notes |
|---|---|---|
| `id` | UUID | |
| `name` | str | |
| `description` | str \| None | |
| `brand_id` | UUID \| None | FK → Brand |
| `status` | enum | `draft` \| `active` \| `archived` — see §4 |
| `created_at` / `updated_at` | datetime | |

No `sku`, `cost_price`, `sell_price`, `category_id`, or `is_active` — all moved out, as below.

### ProductVariant
The actual sellable unit — what Inventory, Sales, and Cart reference from here on (`variant_id`, never `product_id`).

| Field | Type | Notes |
|---|---|---|
| `id` | UUID | |
| `product_id` | UUID | FK → Product |
| `sku` | str | unique |
| `cost_price` | int | cents |
| `sell_price` | int | cents |
| `status` | enum | `draft` \| `active` \| `archived` — independent of the parent Product's status |
| `created_at` / `updated_at` | datetime | |

**Invariant, enforced in the service layer (not the DB):** a Product always has at least one Variant. `create_product` creates the Product and its first Variant in one call — there's no "create a bare product" path. `delete_variant` refuses if it's the last remaining variant for that product (delete the product instead).

**Visibility rule:** a variant is only actually purchasable when `Product.status == active` **and** `Variant.status == active` **and** Inventory reports stock — Product status gates all its variants regardless of their own status.

### ProductCategory
Many-to-many join — a product can now belong to multiple categories. Same shape as `RolePermission`.

| Field | Type |
|---|---|
| `product_id` | UUID, FK → Product |
| `category_id` | UUID, FK → Category |

Composite PK `(product_id, category_id)`.

### Attribute / AttributeValue
Normalized attribute catalog (chosen over loose key-value) — gives typo-proof values and makes "filter by Color = Red" a real query instead of string matching.

**Attribute**

| Field | Type | Notes |
|---|---|---|
| `id` | UUID | |
| `name` | str | e.g. `"Color"`, `"Size"` — unique |

**AttributeValue**

| Field | Type | Notes |
|---|---|---|
| `id` | UUID | |
| `attribute_id` | UUID | FK → Attribute |
| `value` | str | e.g. `"Red"` — unique per `attribute_id` |

### ProductVariantAttribute
Join between a variant and the specific attribute values that define it (e.g. this variant = Color:Red + Size:M).

| Field | Type | Notes |
|---|---|---|
| `variant_id` | UUID | FK → ProductVariant |
| `attribute_id` | UUID | FK → Attribute (denormalized alongside `attribute_value_id` specifically so the constraint below is a plain column constraint, not a join) |
| `attribute_value_id` | UUID | FK → AttributeValue |

Composite PK `(variant_id, attribute_id)` — a variant can't have two values for the same attribute (can't be both Color:Red and Color:Blue at once).

**Invariant, service layer:** no two variants of the same product may share an identical set of attribute-value combinations (no duplicate "Red / M" variant twice under one product).

### ProductImage
Scoped to `ProductVariant`, not `Product` (see the assumption noted above the entity list).

| Field | Type | Notes |
|---|---|---|
| `id` | UUID | |
| `variant_id` | UUID | FK → ProductVariant, **not nullable** |
| `file_path` | str | local disk, per the earlier filesystem-storage decision |
| `order` | int | display order within the variant; the image with the lowest `order` is the primary/cover image — no separate `is_primary` flag |
| `created_at` | datetime | |

A product's "cover image" for listing pages = the lowest-`order` image of its default/first-created variant — resolved at the service/read layer, not stored redundantly. "Setting the primary image" becomes "reorder this image to the front" rather than a distinct flag-toggling action, so there's no risk of two images both marked primary and no unset-previous-primary step to remember.

### Brand
Unchanged: `id, name, description, logo_path, is_active`.

### Category
Unchanged: `id, name, parent_id` (hierarchical, self-referencing).

---

## 3. Status enum

```
ProductStatus / VariantStatus:
  draft     — being set up, not visible or purchasable
  active    — visible, purchasable (subject to stock)
  archived  — no longer sold, kept for order history / reporting
```

Deliberately **not** encoding stock level here (`out_of_stock` is not a status) — availability is a computed fact from Inventory, checked at the time of listing/purchase, not a value someone sets and forgets to update. Product and Variant each carry their own `status` independently — a product can stay `active` while one specific variant (a discontinued color) moves to `archived`.

---

## 4. Relationships (text ERD)

```
Brand 1───* Product *───* Category   (via ProductCategory)
Product 1───* ProductVariant
ProductVariant 1───* ProductImage
ProductVariant *───* AttributeValue  (via ProductVariantAttribute)
Attribute 1───* AttributeValue
```

---

## 5. Events

Following the same pattern established for Role/Permission — factory methods on the entity register the event, services call `uow.track(...)`:

| Entity | Events |
|---|---|
| Product | `ProductCreated`, `ProductUpdated`, `ProductStatusChanged`, `ProductDeleted` |
| ProductVariant | `VariantCreated`, `VariantUpdated`, `VariantStatusChanged`, `VariantDeleted` |
| ProductCategory | `ProductCategoryAssigned`, `ProductCategoryUnassigned` |
| Attribute / AttributeValue | `AttributeCreated`, `AttributeValueCreated` (rarely mutated after creation — no delete/update planned unless a real need shows up) |
| ProductVariantAttribute | `VariantAttributeSet` (assign is really "set the value for this attribute," not a separate assign/revoke pair like RolePermission — a variant either has a value for an attribute or doesn't have that attribute at all) |
| ProductImage | `ProductImageAdded`, `ProductImageRemoved`, `ProductImageReordered` |

`ProductStatusChanged`/`VariantStatusChanged` are separate from `Updated` on purpose — a status transition is a meaningfully different event for a consumer to react to (e.g. Notification caring about a product going `archived`) than a routine field edit, worth being able to subscribe to independently.

---

## 6. Migration note (not a full plan — flagging the shape of the work)

This is a breaking schema change, not additive:

- Every existing `Product` row needs exactly one `ProductVariant` created from its current `sku`/`cost_price`/`sell_price` before those columns can be dropped from `products`.
- Every existing `Product.category_id` becomes one row in `ProductCategory`.
- Existing `ProductImage.product_id` rows need to be reassigned to that product's (new, single) default variant.
- `is_active` → `status`: this is not a mechanical 2-way mapping (`True`→one value, `False`→another). `status` has three real values — every existing row needs an explicit decision among `active`, `draft`, or `archived`, not just a substitution of `True`/`False` for two of the three. A blanket rule (`False` always becomes `archived`) will likely misclassify rows that were actually still `draft` and never finished setup — worth a data review pass before running the migration, not a formula baked into the script.
