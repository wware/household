# Household Database Schema Design

## Architecture Overview

The database schema is designed to be the source of truth, with the server as a business logic layer that wraps the database and exposes a JSON API to the client. This ensures clean separation of concerns:

```
Database (source of truth)
    ↓
Server (business logic + JSON API)
    ↓
Browser (static resources + client JS)
```

## Design Principles

1. **Items as First-Class Objects**: Items (butter, bread, dog food, etc.) are primary entities with their own identity and properties, not just strings in a list. This allows us to:
   - Associate stores with items (many-to-many)
   - Define default quantities per item
   - Define section/category per item (Dairy, Produce, etc.)
   - Track item metadata over time

2. **Stores as First-Class Objects**: Stores are normalized as separate entities with IDs rather than hardcoded enum values. This allows:
   - Dynamic addition of new stores
   - Proper referential integrity
   - Future extensibility (store addresses, hours, etc.)

3. **Many-to-Many Item/Store Relationship**: Items can be available at multiple stores. For example:
   - Butter: available at Trader Joe's, Whole Foods
   - English muffins: only at Trader Joe's
   - Dog food: only at Chewy
   - Rice: no specific store (empty store set)

4. **Unspecified Stores**: Items with an empty store set can come from anywhere. When filtering by store, we include unspecified items (e.g., "Show me what to get at Whole Foods" includes both WFs-specific items and unspecified items).

5. **Section Belongs to Item**: The grocery section (Meat, Dairy, Produce, etc.) is a property of the item itself, not of individual grocery list entries. Once you define "Butter" as a Dairy item, it stays in Dairy regardless of which list or template it appears on.

## ER Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│                         users                                   │
│  ┌───────────────────────────────────────┐                      │
│  │ id (PK)                               │                      │
│  │ name                                  │                      │
│  │ email (UNIQUE)                        │                      │
│  │ created_at                            │                      │
│  └───────────────────────────────────────┘                      │
│         ↑              ↑              ↑                         │
└─────────┼──────────────┼──────────────┼─────────────────────────┘
          │              │              │
          │ user_id (FK) │ user_id (FK) │ user_id (FK)
          │              │              │
┌─────────▼──────────┐   │   ┌──────────▼──────────┐   ┌──────────▼──────────┐
│ appointments       │   │   │ grocery_templates   │   │ grocery_items       │
├────────────────────┤   │   ├─────────────────────┤   ├─────────────────────┤
│ id (PK)            │   │   │ id (PK)             │   │ id (PK)             │
│ title              │   │   │ name                │   │ item_id (FK)        │
│ date               │   │   │ is_default          │   │ quantity (nullable) │
│ type               │   │   │ created_at          │   │ int_quantity        │
│ notes              │   │   │ updated_at          │   │ purchased           │
│ user_id (FK)       │   │   │ user_id (FK)        │   │ created_at          │
│ created_at         │   │   │                     │   │ updated_at          │
│ updated_at         │   │   └─────────────────────┘   │ user_id (FK)        │
└────────────────────┘   │            ↓                └─────────────────────┘
                         │     template_id (FK)
                         │            │
                         │   ┌────────▼──────────────────┐
                         │   │ grocery_template_items    │
                         │   ├───────────────────────────┤
                         │   │ id (PK)                   │
                         │   │ item_id (FK)              │
                         │   │ quantity (nullable)       │
                         │   │ template_id (FK)          │
                         │   │ created_at                │
                         │   └───────────────────────────┘
                         │
┌────────────────────────┴────────────────────┐
│                                             │
│                  items                      │
│  ┌──────────────────────────────────────┐   │
│  │ id (PK)                              │   │
│  │ name (UNIQUE)                        │   │
│  │ default_quantity (nullable)          │   │
│  │ quantity_is_int                      │   │
│  │ section (nullable)                   │   │
│  │ created_at                           │   │
│  │ updated_at                           │   │
│  └──────────────────────────────────────┘   │
│         ↑                                   │
│         │ item_id (FK)                      │
│         │                                   │
│  ┌──────┴──────────────────────┐            │
│  │ item_stores                 │            │
│  ├─────────────────────────────┤            │
│  │ item_id (FK, part of PK)    │            │
│  │ store_id (FK, part of PK) ──┼──────┐     │
│  └─────────────────────────────┘      │     │
│                                       │     │
└───────────────────────────────────────┼─────┘
                                        │
                                        ↓
                              ┌──────────────────┐
                              │ stores           │
                              ├──────────────────┤
                              │ id (PK)          │
                              │ name (UNIQUE)    │
                              │ created_at       │
                              │ updated_at       │
                              └──────────────────┘
```

## Table Definitions

### `users`
- `id` (INTEGER, PK)
- `name` (VARCHAR, NOT NULL)
- `email` (VARCHAR, NOT NULL, UNIQUE)
- `created_at` (TIMESTAMP, NOT NULL, DEFAULT CURRENT_TIMESTAMP)

---

### `appointments`
- `id` (INTEGER, PK)
- `title` (VARCHAR, NOT NULL)
- `date` (TIMESTAMP, NOT NULL)
- `type` (VARCHAR, NOT NULL) - "medical", "pet", "other"
- `notes` (TEXT, nullable)
- `user_id` (INTEGER, NOT NULL, FK to `users.id`)
- `created_at` (TIMESTAMP, NOT NULL, DEFAULT CURRENT_TIMESTAMP)
- `updated_at` (TIMESTAMP, NOT NULL, DEFAULT CURRENT_TIMESTAMP)

**Indexes:**
- `idx_appointments_user_id` on `user_id`
- `idx_appointments_date` on `date`

---

### `tasks`
- `id` (INTEGER, PK)
- `title` (VARCHAR, NOT NULL)
- `category` (VARCHAR, NOT NULL) - "household", "pet", "maintenance", "travel", "other"
- `completed` (BOOLEAN, NOT NULL, DEFAULT FALSE)
- `due_date` (TIMESTAMP, nullable)
- `assigned_to` (INTEGER, nullable, FK to `users.id`)
- `created_at` (TIMESTAMP, NOT NULL, DEFAULT CURRENT_TIMESTAMP)
- `updated_at` (TIMESTAMP, NOT NULL, DEFAULT CURRENT_TIMESTAMP)

**Indexes:**
- `idx_tasks_assigned_to` on `assigned_to`
- `idx_tasks_category` on `category`
- `idx_tasks_completed` on `completed`

---

### `stores`
Store entities for tracking where items can be purchased.

- `id` (INTEGER, PK)
- `name` (VARCHAR, NOT NULL, UNIQUE) - e.g., "TraderJoes", "WholeFoods", "Amazon", "Chewy"
- `created_at` (TIMESTAMP, NOT NULL, DEFAULT CURRENT_TIMESTAMP)
- `updated_at` (TIMESTAMP, NOT NULL, DEFAULT CURRENT_TIMESTAMP)

**Indexes:**
- `idx_stores_name` on `name`
- `idx_stores_created_at` on `created_at`
- `idx_stores_updated_at` on `updated_at`

**Notes:**
- Stores are normalized entities rather than hardcoded enums
- Allows dynamic addition of new stores
- Future extensibility for store metadata (address, hours, etc.)

---

### `items`
Primary table for item definitions (groceries, pet supplies, household items, etc.).

- `id` (INTEGER, PK)
- `name` (VARCHAR, NOT NULL, UNIQUE) - e.g., "butter", "bread", "dog food"
- `default_quantity` (VARCHAR, nullable) - e.g., "1 lb", "1 dozen", "1 bag"
- `quantity_is_int` (BOOLEAN, NOT NULL, DEFAULT FALSE) - TRUE if quantity is naturally an integer (e.g., "2" vs "1 lb")
- `section` (VARCHAR, nullable) - "Meat", "Dairy", "Produce", "Freezer", "Breads", "Other"
- `created_at` (TIMESTAMP, NOT NULL, DEFAULT CURRENT_TIMESTAMP)
- `updated_at` (TIMESTAMP, NOT NULL, DEFAULT CURRENT_TIMESTAMP)

**Indexes:**
- `idx_items_name` on `name`

**Notes:**
- Unique constraint on `name` (assuming shared household item database)
- `default_quantity` is stored as a string to allow flexible formats
- `section` is defined at the item level, not per grocery list entry
- Consider adding `user_id` FK if items should be per-user in the future

---

### `item_stores`
Many-to-many join table defining which stores carry each item.

- `item_id` (INTEGER, NOT NULL, FK to `items.id`, part of composite PK, CASCADE DELETE)
- `store_id` (INTEGER, NOT NULL, FK to `stores.id`, part of composite PK, CASCADE DELETE)
- PK: `(item_id, store_id)`

**Indexes:**
- `idx_item_stores_item_id_store_id` on `(item_id, store_id)`

**Notes:**
- Empty store set (no rows for an item) = item is available anywhere or store is unspecified
- When filtering "What do I need at Whole Foods?", include items where store_id matches OR no stores are defined

---

### `grocery_items`
Individual items on the active grocery list.

- `id` (INTEGER, PK)
- `item_id` (INTEGER, NOT NULL, FK to `items.id`, CASCADE DELETE)
- `quantity` (VARCHAR, nullable) - override `items.default_quantity` if specified
- `int_quantity` (INTEGER, nullable) - parsed integer quantity when applicable
- `purchased` (BOOLEAN, NOT NULL, DEFAULT FALSE)
- `user_id` (INTEGER, NOT NULL, FK to `users.id`)
- `created_at` (TIMESTAMP, NOT NULL, DEFAULT CURRENT_TIMESTAMP)
- `updated_at` (TIMESTAMP, NOT NULL, DEFAULT CURRENT_TIMESTAMP)

**Indexes:**
- `idx_grocery_items_user_id` on `user_id`
- `idx_grocery_items_item_id` on `item_id`
- `idx_grocery_items_purchased` on `purchased`

**Notes:**
- No `section` column - comes from `items.section`
- No `store` column - comes from `item_stores` join table
- `quantity` overrides the item's default if specified

---

### `grocery_templates`
Templates for bulk-adding items to the grocery list.

- `id` (INTEGER, PK)
- `name` (VARCHAR, NOT NULL)
- `is_default` (BOOLEAN, NOT NULL, DEFAULT FALSE)
- `user_id` (INTEGER, NOT NULL, FK to `users.id`)
- `created_at` (TIMESTAMP, NOT NULL, DEFAULT CURRENT_TIMESTAMP)
- `updated_at` (TIMESTAMP, NOT NULL, DEFAULT CURRENT_TIMESTAMP)

**Indexes:**
- `idx_grocery_templates_user_id` on `user_id`
- `idx_grocery_templates_is_default` on `is_default`

---

### `grocery_template_items`
Items within a grocery template.

- `id` (INTEGER, PK)
- `item_id` (INTEGER, NOT NULL, FK to `items.id`, CASCADE DELETE)
- `quantity` (VARCHAR, nullable) - override `items.default_quantity` if specified
- `template_id` (INTEGER, NOT NULL, FK to `grocery_templates.id`, CASCADE DELETE)
- `created_at` (TIMESTAMP, NOT NULL, DEFAULT CURRENT_TIMESTAMP)

**Indexes:**
- `idx_grocery_template_items_template_id` on `template_id`
- `idx_grocery_template_items_item_id` on `item_id`

**Notes:**
- No `section` column - comes from `items.section`
- No `store` column - comes from `item_stores` join table
- No `updated_at` - template items are treated as immutable; re-create if changes needed

---

## API Implications

### Stores Endpoints
```
GET    /api/stores              - List all stores
POST   /api/stores              - Create new store
GET    /api/stores/{id}         - Get store by ID
PUT    /api/stores/{id}         - Update store
DELETE /api/stores/{id}         - Delete store (if no items reference it)
```

### Items Endpoints
```
GET    /api/items                      - List all items
POST   /api/items                      - Create new item with stores and section
GET    /api/items/{id}                 - Get item with stores
PUT    /api/items/{id}                 - Update item (name, quantity, section, stores)
DELETE /api/items/{id}                 - Delete item
GET    /api/items?store_id={id}        - Filter items by store
GET    /api/items?section={section}    - Filter items by section
```

### Grocery Items Endpoints
```
GET    /api/grocery-items?user_id={id}            - Get user's grocery list
GET    /api/grocery-items?user_id={id}&store_id={id}  - Filter by store (includes unspecified)
POST   /api/grocery-items                         - Create with item_id, optional quantity override
PUT    /api/grocery-items/{id}                    - Update quantity or purchased status
DELETE /api/grocery-items/{id}                    - Remove from list
```

### Templates Endpoints
```
GET    /api/grocery-templates?user_id={id}        - List user's templates
POST   /api/grocery-templates                     - Create template
GET    /api/grocery-templates/{id}                - Get template with items
PUT    /api/grocery-templates/{id}                - Update template metadata
DELETE /api/grocery-templates/{id}                - Delete template
POST   /api/grocery-templates/{id}/apply          - Apply template to grocery list
```

### Appointments Endpoints
```
GET    /api/appointments?user_id={id}             - List user's appointments
POST   /api/appointments                          - Create appointment
GET    /api/appointments/{id}                     - Get appointment
PUT    /api/appointments/{id}                     - Update appointment
DELETE /api/appointments/{id}                     - Delete appointment
```

### Tasks Endpoints
```
GET    /api/tasks?user_id={id}                    - List user's tasks
GET    /api/tasks?assigned_to={id}                - Filter by assignee
GET    /api/tasks?category={category}             - Filter by category
POST   /api/tasks                                 - Create task
PUT    /api/tasks/{id}                            - Update task
DELETE /api/tasks/{id}                            - Delete task
```

---

## Example Data

```sql
-- Stores
stores:
  id=1, name="TraderJoes"
  id=2, name="WholeFoods"
  id=3, name="Amazon"
  id=4, name="Chewy"

-- Items
items:
  id=1, name="Butter", default_quantity="1 lb", section="Dairy", quantity_is_int=false
  id=2, name="English muffins", default_quantity="1 package", section="Breads", quantity_is_int=false
  id=3, name="Dog food (large bag)", default_quantity="1", section="Other", quantity_is_int=true
  id=4, name="Rice", default_quantity="1 lb", section="Other", quantity_is_int=false

-- Item-Store associations
item_stores:
  (item_id=1, store_id=1)  -- Butter at Trader Joe's
  (item_id=1, store_id=2)  -- Butter at Whole Foods
  (item_id=2, store_id=1)  -- English muffins at Trader Joe's only
  (item_id=3, store_id=4)  -- Dog food at Chewy only
  -- No entries for Rice (id=4) = available anywhere

-- Grocery list
grocery_items:
  id=10, item_id=1, quantity=NULL, int_quantity=NULL, purchased=false, user_id=1
         -- Butter, will use default "1 lb"
  id=11, item_id=2, quantity=NULL, int_quantity=NULL, purchased=false, user_id=1
         -- English muffins
  id=12, item_id=3, quantity="2", int_quantity=2, purchased=false, user_id=1
         -- 2 bags of dog food (override default)
  id=13, item_id=4, quantity=NULL, int_quantity=NULL, purchased=false, user_id=1
         -- Rice (no specific store)
```

**Filtering Examples:**

`GET /api/grocery-items?user_id=1&store_id=2` (Whole Foods) returns items 10, 13:
- Item 10 (Butter): explicitly available at Whole Foods (store_id=2)
- Item 13 (Rice): no store specified, included in all store queries
- Item 11 (English muffins): NOT included (only at Trader Joe's)
- Item 12 (Dog food): NOT included (only at Chewy)

`GET /api/grocery-items?user_id=1&store_id=1` (Trader Joe's) returns items 10, 11, 13:
- Item 10 (Butter): available at Trader Joe's
- Item 11 (English muffins): available at Trader Joe's
- Item 13 (Rice): unspecified store
- Item 12 (Dog food): NOT included (only at Chewy)

---

## Notes

- Items are shared across the household (no per-user items)
- Section is defined at the item level for consistency
- Stores are normalized for extensibility
- Empty store associations mean "available anywhere"
- Quantity can be overridden per grocery list entry
- `quantity_is_int` helps with parsing and aggregation logic
- Default quantities are strings to allow flexible formats (e.g., "2-3 lbs", "as needed", "1 package")
