# Store-Up Architecture & API Documentation

Welcome to the internal technical documentation for **Store-Up**! 

This site serves as the single source of truth for the API specifications, data models, and event-driven architectural design of the various domains within the application.

## Architecture Overview

Store-Up is built using a strict **Domain-Driven Design (DDD)** architecture on top of Flask and SQLAlchemy. 
The codebase is structured to ensure domains are decoupled, communicating through an Event Bus when cross-domain reactions are necessary.

- **Entities**: Pure Python dataclasses representing business concepts.
- **Repositories**: SQL-backed stores interacting with a generic Unit of Work.
- **Services**: Business logic orchestrators enforcing authorization and emitting domain events.
- **Routes**: Thin HTTP layers utilizing Pydantic schemas for strict request/response validation.

## Domains

Explore the documentation for each of our bounded contexts:

- **[Accounts](domains/accounts.md)**: User identity, profile management, credentials, and role associations.
- **[RBAC](domains/rbac.md)**: Role-Based Access Control, managing the granular permissions available in the system.
- **[Auth](domains/auth.md)**: Authentication token issuance and lifecycle management.
- **[Catalog](domains/catalog.md)**: Product and category management.
- **[Stock](domains/stock.md)**: Inventory tracking and stock movements.
- **[Sale](domains/sale.md)**: Point-of-sale transactions and checkout processing.

*(Note: The Billing domain is currently under active development.)*
