-- Household Database Schema
-- Database design for household AI assistant tracking grocery items, templates, appointments, and tasks

-- ============================================================================
-- Users
-- ============================================================================

CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR NOT NULL,
    email VARCHAR NOT NULL UNIQUE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- Appointments
-- ============================================================================

CREATE TABLE appointments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title VARCHAR NOT NULL,
    date TIMESTAMP NOT NULL,
    type VARCHAR NOT NULL,  -- "medical", "pet", "other"
    notes TEXT,
    user_id INTEGER NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE INDEX idx_appointments_user_id ON appointments(user_id);
CREATE INDEX idx_appointments_date ON appointments(date);

-- ============================================================================
-- Tasks
-- ============================================================================

CREATE TABLE tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title VARCHAR NOT NULL,
    category VARCHAR NOT NULL,  -- "household", "pet", "maintenance", "travel", "other"
    completed BOOLEAN NOT NULL DEFAULT FALSE,
    due_date TIMESTAMP,
    assigned_to INTEGER,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (assigned_to) REFERENCES users(id)
);

CREATE INDEX idx_tasks_assigned_to ON tasks(assigned_to);
CREATE INDEX idx_tasks_category ON tasks(category);
CREATE INDEX idx_tasks_completed ON tasks(completed);

-- ============================================================================
-- Food Items (NEW)
-- ============================================================================

CREATE TABLE food_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR NOT NULL UNIQUE,
    default_quantity VARCHAR,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_food_items_name ON food_items(name);

-- ============================================================================
-- Food Item Stores (NEW) - Many-to-Many Relationship
-- ============================================================================

CREATE TABLE food_item_stores (
    food_item_id INTEGER NOT NULL,
    store VARCHAR NOT NULL,  -- "TJs", "WFs", "Amazon", "Chewy"
    PRIMARY KEY (food_item_id, store),
    FOREIGN KEY (food_item_id) REFERENCES food_items(id) ON DELETE CASCADE
);

CREATE INDEX idx_food_item_stores_store ON food_item_stores(store);

-- ============================================================================
-- Grocery Items (MODIFIED)
-- ============================================================================

CREATE TABLE grocery_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    food_item_id INTEGER NOT NULL,
    quantity VARCHAR,  -- Override default_quantity if specified
    purchased BOOLEAN NOT NULL DEFAULT FALSE,
    section VARCHAR,  -- "Meat", "Dairy", "Produce", "Freezer", "Breads", "Other"
    user_id INTEGER NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (food_item_id) REFERENCES food_items(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE INDEX idx_grocery_items_user_id ON grocery_items(user_id);
CREATE INDEX idx_grocery_items_food_item_id ON grocery_items(food_item_id);
CREATE INDEX idx_grocery_items_purchased ON grocery_items(purchased);

-- ============================================================================
-- Grocery Templates
-- ============================================================================

CREATE TABLE grocery_templates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR NOT NULL,
    is_default BOOLEAN NOT NULL DEFAULT FALSE,
    user_id INTEGER NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE INDEX idx_grocery_templates_user_id ON grocery_templates(user_id);
CREATE INDEX idx_grocery_templates_is_default ON grocery_templates(is_default);

-- ============================================================================
-- Grocery Template Items (MODIFIED)
-- ============================================================================

CREATE TABLE grocery_template_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    food_item_id INTEGER NOT NULL,
    quantity VARCHAR,  -- Override default_quantity if specified
    section VARCHAR,  -- "Meat", "Dairy", "Produce", "Freezer", "Breads", "Other"
    template_id INTEGER NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (food_item_id) REFERENCES food_items(id) ON DELETE CASCADE,
    FOREIGN KEY (template_id) REFERENCES grocery_templates(id) ON DELETE CASCADE
);

CREATE INDEX idx_grocery_template_items_template_id ON grocery_template_items(template_id);
CREATE INDEX idx_grocery_template_items_food_item_id ON grocery_template_items(food_item_id);
