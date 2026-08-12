# Shop Management API — Design

## 1. Core Entities

**Account** — `id, first_name, last_name, birth_date, status (active|suspended), created_at, updated_at`
No password, no role, no login fields here — identity only.

**Credential** — `id, account_id, username, email, password_hash, last_login_at, created_at, updated_at`
Separated so an account's identity (name, DOB) is independent of its login info, and resetting a password or changing a username never touches identity or role data.

**Role** — `id, name, description, is_system (bool)`
`is_system` roles (e.g. `admin`) can't be deleted. Beyond that, roles are entirely user-definable.

**Permission** — `id, domain, entity, action, description`
The RBAC unit, keyed as `domain.entity.action` — e.g. `inventory.product.update`, `sales.sale.void`, `reports.revenue.read`. Permissions are system-defined (they map 1:1 to real API capabilities); roles are just named bundles of them.

**RolePermission** — `role_id, permission_id` (join table)

**AccountRole** — `account_id, role_id, domain (optional scope), assigned_at, assigned_by`
The optional `domain` lets the same role (e.g. "manager") be granted scoped to just `inventory` for one account, or globally for another.

**Product** — `id, sku, name, description, category_id, brand_id, cost_price, sell_price, is_active, created_at, updated_at`

**Brand** — `id, name, description, logo_path, is_active`
`logo_path` is a local disk path, same pattern as `ProductImage.file_path` — uploaded via multipart, served through the static file route.

**ProductImage** — `id, product_id, file_path, is_primary, sort_order, created_at`
A product can have multiple images; `is_primary` marks the one used in listing/thumbnail views. `file_path` is the path on local disk (e.g. `/uploads/products/{uuid}.jpg`), served via a static file route rather than a cloud URL.

**Inventory** — `id, product_id, stock_qty, reorder_level, updated_at`
Split out from Product so catalog data (name, price, image) and stock levels can change independently — e.g. later supporting multiple warehouses/locations just means multiple Inventory rows per product.

**Category** — `id, name, parent_id (optional)`

**Sale** — `id, account_id, customer_id (optional), status (completed|voided|refunded), payment_method, subtotal, discount, tax, total, created_at`

**SaleItem** — `id, sale_id, product_id, quantity, unit_price, subtotal`

**Notification** — `id, type (alert|warning|info), category (low_stock|sale|system), message, related_entity_type, related_entity_id, is_read, created_at`

---

## 2. Accounts & Credentials

```
POST   /accounts                        create account (identity only — no login info)
GET    /accounts                        ?search=&status=&page=
GET    /accounts/{id}
PUT    /accounts/{id}
DELETE /accounts/{id}                   soft delete (status=suspended)

POST   /accounts/{id}/credentials       set the account's login credential {username, email, password}
GET    /accounts/{id}/credentials       returns username, email, last_login_at (never password_hash)
PUT    /accounts/{id}/credentials       update username/email/password
```

## 3. Auth

```
POST   /auth/login       {username_or_email, password} -> looks up Credential, validates password_hash -> access + refresh token (JWT claims include resolved permissions)
POST   /auth/refresh
POST   /auth/logout
```

## 4. RBAC — Roles & Permissions

```
GET    /permissions                     ?domain=&entity=        list available domain.entity.action keys (system-defined)

POST   /roles                           {name, description}     create a custom role
GET    /roles
GET    /roles/{id}
PUT    /roles/{id}
DELETE /roles/{id}                      blocked if is_system=true

GET    /roles/{id}/permissions
POST   /roles/{id}/permissions          {permission_ids: [...]}  attach permissions to role
DELETE /roles/{id}/permissions/{permission_id}
```

```
POST   /accounts/{id}/roles             {role_id, domain?}       assign a role (optionally scoped)
GET    /accounts/{id}/roles
DELETE /accounts/{id}/roles/{role_id}
GET    /accounts/{id}/permissions       effective, resolved permission set — use this to assess what an account can actually do
```

Access control check at request time: `has_permission(account, domain, entity, action)` — resolved by unioning permissions across all of the account's roles (respecting any domain scoping).

---

## 5. Products

```
POST   /products                     requires inventory.product.create
GET    /products                     ?search=&category_id=&brand_id=&page=&limit=&sort=
GET    /products/{id}
PUT    /products/{id}                full update
PATCH  /products/{id}                partial update (e.g. price, brand_id)
DELETE /products/{id}                soft delete (is_active=false)
```

```
POST   /categories
GET    /categories
PUT    /categories/{id}
DELETE /categories/{id}
```

```
POST   /brands                       {name, description}
GET    /brands                       ?search=&page=
GET    /brands/{id}
PUT    /brands/{id}
DELETE /brands/{id}                  soft delete (is_active=false); blocked/warned if products reference it

POST   /brands/{id}/logo             multipart/form-data upload {file} -> saved to disk, logo_path updated
DELETE /brands/{id}/logo             removes file from disk, clears logo_path
```

```
POST   /products/{id}/images          multipart/form-data upload {file, is_primary?} -> saved to disk, ProductImage row created
GET    /products/{id}/images          returns file_path (or a served /files/... URL) per image
PATCH  /products/{id}/images/{image_id}    e.g. set is_primary, reorder (sort_order)
DELETE /products/{id}/images/{image_id}    removes DB row and deletes the file from disk
```

---

## 6. Inventory

```
GET    /inventory/{product_id}              current stock_qty + reorder_level for a product
POST   /inventory/{product_id}/adjust        {delta, reason}  -- restock / correction / sale-driven decrement
GET    /inventory/{product_id}/history       audit trail of qty changes
GET    /inventory                            ?low_stock=true&page=&limit=   list across all products
```

---

## 7. Sales

```
POST   /sales
```
Body:
```json
{
  "items": [{"product_id": 12, "quantity": 2}],
  "payment_method": "cash",
  "discount": 0
}
```
Server computes prices from current product price, decrements the matching Inventory row atomically (reject if insufficient), triggers low-stock notification if `stock_qty <= reorder_level` after the sale.

```
GET    /sales                ?from=&to=&account_id=&product_id=&status=&page=&limit=
GET    /sales/{id}
POST   /sales/{id}/void      requires sales.sale.void, restores stock
```

---

## 8. Reports

```
GET /reports/products/top-selling      ?from=&to=&limit=
GET /reports/products/low-stock        (sourced from Inventory)
GET /reports/products/slow-moving      ?since=

GET /reports/sales                     ?period=daily|weekly|monthly&from=&to=
GET /reports/sales/by-account          ?from=&to=
GET /reports/sales/by-product          ?from=&to=

GET /reports/revenue                   ?group_by=product|period|account|category&from=&to=&interval=day|week|month
```
`/reports/revenue` returns a series, e.g.:
```json
{
  "group_by": "period",
  "interval": "day",
  "data": [
    {"key": "2026-08-10", "revenue": 452.30, "cost": 210.00, "profit": 242.30, "sales_count": 14}
  ]
}
```

---

## 9. Notifications

```
GET    /notifications           ?type=alert|warning&is_read=false&page=
PATCH  /notifications/{id}/read
PATCH  /notifications/read-all
DELETE /notifications/{id}
```
Generated server-side (not user-created) by triggers:
- `low_stock` warning when Inventory `stock_qty <= reorder_level`
- `out_of_stock` alert when Inventory `stock_qty == 0`
- optional: daily sales summary, void/refund alerts to accounts with `sales.sale.void` permission

---

## 10. Conventions

- **Pagination**: `?page=1&limit=20` → response includes `{data, page, limit, total, total_pages}`
- **Filtering/sorting**: query params, e.g. `?sort=-created_at`
- **Errors**: consistent shape `{"error": {"code": "PRODUCT_NOT_FOUND", "message": "..."}}`
- **Money**: store as integer cents to avoid float rounding errors
- **Concurrency**: Inventory decrement on sale must be a transaction (row lock or optimistic `version` field) to prevent overselling
- **Soft deletes**: products are deactivated, not hard-deleted, to preserve historical sale records
- **Filesystem uploads**: product images and brand logos are uploaded as multipart form data, written to local disk (e.g. under an `/uploads/` directory outside version control), and served back through a static file route — no cloud object store involved. Validate file type/size server-side and generate a random filename (don't trust the client-supplied name) to avoid path traversal or collisions.

---

## 11. Suggested Stack-Agnostic Flow

1. Sale creation → validate stock via Inventory → transaction: insert sale + sale_items, decrement Inventory.stock_qty → check thresholds → emit notification(s).
2. Reports are read-only aggregation queries (SQL `GROUP BY` / materialized views for heavy report endpoints if volume is high).
3. Notifications table is append-only + a `is_read` flag; a background job or the sale-transaction hook creates new rows.
