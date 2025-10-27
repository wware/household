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

1. **Food Items as First-Class Objects**: Food items (butter, bread, etc.) are primary entities with their own identity and properties, not just strings in a list. This allows us to:
   - Associate stores with items (many-to-many)
   - Define default quantities per item
   - Track item metadata over time

2. **Many-to-Many Item/Store Relationship**: Items can be available at multiple stores. For example:
   - Butter: available at TJs, WFs
   - English muffins: only at TJs
   - Dog food: only at Chewy
   - Rice: no specific store (empty store set)

3. **Unspecified Stores**: Items with an empty store set can come from anywhere. When filtering by store, we include unspecified items (e.g., "Show me what to get at Whole Foods" includes both WFs-specific items and unspecified items).

4. **No Store Enum for Grocery Items**: Individual grocery list items no longer have a store column. The store information comes from the associated FoodItem. This is informational only and doesn't constrain where you shop on a given trip.

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
│         ↑              ↑              ↑                          │
└─────────┼──────────────┼──────────────┼──────────────────────────┘
          │              │              │
          │ user_id (FK) │ user_id (FK) │ user_id (FK)
          │              │              │
┌─────────▼──────────┐   │   ┌──────────▼──────────┐   ┌──────────▼──────────┐
│ appointments       │   │   │ grocery_templates   │   │ grocery_items       │
├────────────────────┤   │   ├─────────────────────┤   ├─────────────────────┤
│ id (PK)            │   │   │ id (PK)             │   │ id (PK)             │
│ title              │   │   │ name                │   │ food_item_id (FK)   │
│ date               │   │   │ is_default          │   │ quantity (nullable) │
│ type               │   │   │ created_at          │   │ purchased           │
│ notes              │   │   │ updated_at          │   │ created_at          │
│ user_id (FK)       │   │   │ user_id (FK)        │   │ updated_at          │
│ created_at         │   │   │                     │   │ user_id (FK)        │
│ updated_at         │   │   └─────────────────────┘   └─────────────────────┘
└────────────────────┘   │            ↓
                         │     template_id (FK)
                         │            │
                         │   ┌────────▼──────────────────┐
                         │   │ grocery_template_items     │
                         │   ├────────────────────────────┤
                         │   │ id (PK)                    │
                         │   │ food_item_id (FK)          │
                         │   │ quantity (nullable)        │
                         │   │ template_id (FK)           │
                         │   │ created_at                 │
                         │   └────────────────────────────┘
                         │
┌────────────────────────┴──────────────────────────────────────┐
│                                                               │
│                        food_items                             │
│  ┌────────────────────────────────────────┐                   │
│  │ id (PK)                                │                   │
│  │ name                                   │                   │
│  │ default_quantity (nullable, e.g. "1") │                   │
│  │ created_at                             │                   │
│  │ updated_at                             │                   │
│  └────────────────────────────────────────┘                   │
│         ↑                                                      │
│         │ food_item_id (FK)                                   │
│         │                                                      │
│  ┌──────┴────────────────────────┐                            │
│  │ food_item_stores               │                            │
│  ├────────────────────────────────┤                            │
│  │ food_item_id (FK, part of PK)  │                            │
│  │ store (Enum, part of PK)       │                            │
│  │   - "TJs"                      │                            │
│  │   - "WFs"                      │                            │
│  │   - "Amazon"                   │                            │
│  │   - "Chewy"                    │                            │
│  └────────────────────────────────┘                            │
│                                                               │
└───────────────────────────────────────────────────────────────┘
```

## Table Definitions

### `users` (existing, unchanged)
- `id` (INTEGER, PK)
- `name` (VARCHAR)
- `email` (VARCHAR, UNIQUE)
- `created_at` (TIMESTAMP)

---

### `food_items` (NEW)
Primary table for food/item definitions.

- `id` (INTEGER, PK)
- `name` (VARCHAR, NOT NULL) - e.g., "butter", "bread", "dog food"
- `default_quantity` (VARCHAR, nullable) - e.g., "1 lb", "1 dozen", "1 bag"
- `created_at` (TIMESTAMP)
- `updated_at` (TIMESTAMP)

**Notes:**
- Unique constraint on `name` (within a household context; consider adding `user_id` if items are per-user)
- `default_quantity` is stored as a string to allow flexible formats

---

### `food_item_stores` (NEW, many-to-many join table)
Defines which stores carry each food item.

- `food_item_id` (INTEGER, FK to `food_items.id`, part of composite PK)
- `store` (VARCHAR/ENUM, part of composite PK) - values: "TJs", "WFs", "Amazon", "Chewy"
- PK: `(food_item_id, store)`

**Notes:**
- Empty store set = item is available anywhere or store is unspecified
- When filtering "What do I need at Whole Foods?", return items where store="WFs" OR no stores are defined

---

### `grocery_items` (MODIFIED)
Individual items on the working grocery list.

**Old schema:**
```
id, name, quantity, purchased, store, section, user_id, created_at, updated_at
```

**New schema:**
```
id, food_item_id, quantity, purchased, section, user_id, created_at, updated_at
```

- `id` (INTEGER, PK)
- `food_item_id` (INTEGER, FK to `food_items.id`, NOT NULL)
- `quantity` (VARCHAR, nullable) - override default if specified, otherwise use food_item.default_quantity
- `purchased` (BOOLEAN, default FALSE)
- `section` (ENUM) - "Meat", "Dairy", "Produce", "Freezer", "Breads", "Other"
- `user_id` (INTEGER, FK to `users.id`, NOT NULL)
- `created_at` (TIMESTAMP)
- `updated_at` (TIMESTAMP)

**Changes:**
- Replace `store` column with `food_item_id` FK
- Remove `name` column (comes from food_item)
- `section` remains (separate from store, applies to the item itself)

---

### `grocery_templates` (existing, unchanged)
Templates for bulk-adding items to the grocery list.

- `id` (INTEGER, PK)
- `name` (VARCHAR, NOT NULL)
- `is_default` (BOOLEAN, default FALSE)
- `user_id` (INTEGER, FK to `users.id`, NOT NULL)
- `created_at` (TIMESTAMP)
- `updated_at` (TIMESTAMP)

---

### `grocery_template_items` (MODIFIED)
Items within a template.

**Old schema:**
```
id, name, quantity, store, section, template_id, created_at
```

**New schema:**
```
id, food_item_id, quantity, section, template_id, created_at
```

- `id` (INTEGER, PK)
- `food_item_id` (INTEGER, FK to `food_items.id`, NOT NULL)
- `quantity` (VARCHAR, nullable) - override default if specified
- `section` (ENUM) - "Meat", "Dairy", "Produce", "Freezer", "Breads", "Other"
- `template_id` (INTEGER, FK to `grocery_templates.id`, NOT NULL, CASCADE DELETE)
- `created_at` (TIMESTAMP)

**Changes:**
- Replace `name` column with `food_item_id` FK
- Replace `store` column with access to food_item.stores
- Remove `updated_at` (templates items are immutable; re-create if changes needed)

---

### `StoreType` Enum (MODIFIED)
Update the Python enum to remove "Either" and "Neither".

**Old values:**
```
TRADER_JOES = "TJs"
WHOLE_FOODS = "WFs"
AMAZON = "Amazon"
CHEWY = "Chewy"
EITHER = "Either"
NEITHER = "Neither"
```

**New values:**
```
TRADER_JOES = "TJs"
WHOLE_FOODS = "WFs"
AMAZON = "Amazon"
CHEWY = "Chewy"
```

---

## Migration Path

1. Create new `food_items` table
2. Create new `food_item_stores` join table
3. Seed `food_items` with existing item names from `grocery_items` and `grocery_template_items`
4. Seed `food_item_stores` based on old store values (handle "Either" → multiple stores, "Neither" → no stores)
5. Add `food_item_id` column to `grocery_items` and `grocery_template_items`
6. Populate `food_item_id` in both tables
7. Drop `store` and `name` columns from `grocery_items`
8. Drop `store` and `name` columns from `grocery_template_items`
9. Update Python ORM models and Pydantic schemas
10. Remove "Either" and "Neither" from `StoreType` enum

---

## API Implications

### Food Items Endpoints (NEW)
```
GET    /api/food-items              - List all food items
POST   /api/food-items              - Create new food item with stores
GET    /api/food-items/{id}         - Get food item with stores
PUT    /api/food-items/{id}         - Update food item and stores
DELETE /api/food-items/{id}         - Delete food item
```

### Grocery Items (MODIFIED)
```
GET    /api/grocery-items?user_id=X&store=WFs  - Filter by store (includes unspecified)
POST   /api/grocery-items                      - Create with food_item_id
PUT    /api/grocery-items/{id}                 - Update quantity, section, purchased status
```

### Templates (MODIFIED)
```
POST   /api/grocery-templates/{id}/clone?items=1,2,3  - Clone specific items by ID
```

---

## Example Data

```
food_items:
  id=1, name="Butter", default_quantity="1 lb"
  id=2, name="English muffins", default_quantity="1 package"
  id=3, name="Dog food (large bag)", default_quantity="1"

food_item_stores:
  (1, "TJs"), (1, "WFs")           -- Butter available at both
  (2, "TJs")                        -- English muffins only at TJs
  (3, "Chewy")                      -- Dog food only at Chewy
  -- No entries for item 4 = unspecified store

grocery_items (working list):
  id=10, food_item_id=1, quantity=NULL, purchased=false, user_id=1
        -- Butter, will use default "1 lb"
  id=11, food_item_id=2, quantity=NULL, purchased=false, user_id=1
        -- English muffins
  id=12, food_item_id=3, quantity="2", purchased=false, user_id=1
        -- 2 bags of dog food (override default)
```

Filtering "GET /api/grocery-items?user_id=1&store=WFs" returns items 10 and 11:
- Item 10 (Butter): explicitly available at WFs
- Item 11 (English muffins): no explicit store, so included in unspecified set
- Item 12 (Dog food): NOT included (only at Chewy)

---

## Notes

- Consider adding a `user_id` to `food_items` if items should be per-user in the future. Currently assuming a shared household food item database.
- `SectionType` enum remains unchanged and applies to the item on the list, not to the food item definition.
- Default quantities are strings to allow flexibility (e.g., "2-3 lbs", "as needed", "1 package").
