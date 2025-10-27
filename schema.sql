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
-- Providers (Doctors, Vets, Service Providers)
-- ============================================================================

CREATE TABLE providers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR NOT NULL,
    phone VARCHAR,
    email VARCHAR,
    website VARCHAR,
    address TEXT,  -- Multi-line physical address
    info TEXT,     -- Free-form description/info field
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_providers_name ON providers(name);

-- ============================================================================
-- Appointments
-- ============================================================================

CREATE TABLE appointments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title VARCHAR NOT NULL,
    date TIMESTAMP NOT NULL,
    type VARCHAR NOT NULL,  -- "medical", "pet", "other"
    notes TEXT,
    provider_id INTEGER,  -- Reference to provider (doctor, vet, etc.)
    patient_name VARCHAR,  -- Name of patient (user name or pet name)
    created_by INTEGER NOT NULL,  -- User who created the appointment
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (provider_id) REFERENCES providers(id),
    FOREIGN KEY (created_by) REFERENCES users(id)
);

CREATE INDEX idx_appointments_provider_id ON appointments(provider_id);
CREATE INDEX idx_appointments_created_by ON appointments(created_by);
CREATE INDEX idx_appointments_date ON appointments(date);
CREATE INDEX idx_appointments_patient_name ON appointments(patient_name);

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
-- Stores
-- ============================================================================

CREATE TABLE stores (
    -- Examples: "TraderJoes", "WholeFoods", "Amazon", "Chewy"
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR NOT NULL UNIQUE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_stores_name ON stores(name); -- Unique constraint on name
CREATE INDEX idx_stores_created_at ON stores(created_at);
CREATE INDEX idx_stores_updated_at ON stores(updated_at);

-- ============================================================================
-- Items
-- ============================================================================

CREATE TABLE items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR NOT NULL UNIQUE,
    default_quantity VARCHAR,
    quantity_is_int BOOLEAN NOT NULL DEFAULT FALSE,  -- TRUE if quantity is naturally an integer (e.g., "2" vs "1 lb")
    section VARCHAR,  -- "Meat", "Dairy", "Produce", "Freezer", "Breads", "Other"
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_items_name ON items(name);

-- ============================================================================
-- Item Stores - Many-to-Many Relationship
-- ============================================================================

CREATE TABLE item_stores (
    item_id INTEGER NOT NULL,
    store_id INTEGER NOT NULL,
    PRIMARY KEY (item_id, store_id),
    FOREIGN KEY (item_id) REFERENCES items(id) ON DELETE CASCADE,
    FOREIGN KEY (store_id) REFERENCES stores(id) ON DELETE CASCADE
);

CREATE INDEX idx_item_stores_item_id_store_id ON item_stores(item_id, store_id);

-- ============================================================================
-- Grocery Items
-- ============================================================================

CREATE TABLE grocery_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_id INTEGER NOT NULL,
    quantity VARCHAR,  -- Override default_quantity if specified
    int_quantity INTEGER,  -- Parsed integer quantity when applicable
    purchased BOOLEAN NOT NULL DEFAULT FALSE,
    user_id INTEGER NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (item_id) REFERENCES items(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE INDEX idx_grocery_items_user_id ON grocery_items(user_id);
CREATE INDEX idx_grocery_items_item_id ON grocery_items(item_id);
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
-- Grocery Template Items
-- ============================================================================

CREATE TABLE grocery_template_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_id INTEGER NOT NULL,
    quantity VARCHAR,  -- Override default_quantity if specified
    template_id INTEGER NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (item_id) REFERENCES items(id) ON DELETE CASCADE,
    FOREIGN KEY (template_id) REFERENCES grocery_templates(id) ON DELETE CASCADE
);

CREATE INDEX idx_grocery_template_items_template_id ON grocery_template_items(template_id);
CREATE INDEX idx_grocery_template_items_item_id ON grocery_template_items(item_id);
