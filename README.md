# Household AI Assistant

A shared AI assistant for household coordination, tracking groceries, appointments, tasks, and more.

## Features

- **Web Interface**: Responsive browser-based UI for desktop and mobile
  - Intuitive navigation with tab-based sections
  - Settings gear icon for admin access and API documentation
  - Auto-refresh every 10 seconds
  - Works on Chrome and Firefox
  - Quick access to interactive API docs (Swagger & ReDoc)

- **Grocery Management**: Track items, organize by store and section, create reusable templates
  - Dropdown-based item selection with auto-fill quantities
  - Store filter to see only items available at specific stores
  - Template system for recurring grocery lists
  - Mark items as purchased

- **Appointments**: Schedule medical, pet, and other appointments
  - Calendar view with FullCalendar integration
  - Provider management with contact details
  - Filter by user or patient name

- **Tasks**: Manage household tasks with categories and assignments
  - Categories: household, maintenance, shopping, personal, work, health
  - Due dates and completion tracking
  - Assign tasks to household members

- **Admin Panel**: Centralized management interface
  - Stores: Add/remove grocery stores
  - Items: Manage item catalog with stores, sections, and default quantities
  - Providers: Track medical/dental/vet provider information
  - Templates: View and manage grocery list templates

- **Multi-user**: Shared between household members with per-user preferences

## Project Structure

```
household/
├── schema.sql              # Database schema definition
├── DB_SCHEMA_DESIGN.md     # Database design documentation
├── requirements.txt        # Python dependencies
├── client/                 # Web interface (HTML/CSS/JS)
│   ├── index.html         # Main application UI
│   ├── app.js             # Frontend JavaScript
│   ├── admin.html         # Admin panel UI
│   └── admin.js           # Admin panel JavaScript
├── server/                 # FastAPI server
│   ├── __init__.py
│   ├── main.py            # Main application entry point
│   ├── database.py        # Database connection utilities
│   ├── models.py          # Pydantic models
│   └── routers/           # API endpoints
│       ├── stores.py
│       ├── items.py
│       ├── grocery_items.py
│       ├── templates.py
│       ├── providers.py
│       ├── appointments.py
│       └── tasks.py
└── household.db           # SQLite database (created at runtime)
```

## Setup

### Prerequisites

- Python 3.12 or 3.13
- `uv` (preferred) or `pip`

### Installation

1. **Set up virtual environment and install dependencies:**

   ```bash
   # Using uv (recommended)
   uv venv
   source .venv/bin/activate
   uv pip install -r requirements.txt

   # Or using pip
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Initialize the database:**

   ```bash
   python -m server.database
   ```

   To reset the database (WARNING: destroys all data):

   ```bash
   python -m server.database --reset
   ```

### Running the Server

```bash
# Start the development server
uvicorn server.main:app --reload --host 0.0.0.0 --port 3000
```

The application will be available at:
- **Web UI**: http://localhost:3000 (main interface)
- **Admin Panel**: http://localhost:3000/admin.html (or via settings gear icon)
- API docs: http://localhost:3000/docs
- Alternative docs: http://localhost:3000/redoc

## API Endpoints

### Stores
- `GET /api/stores` - List all stores
- `POST /api/stores` - Create a store
- `GET /api/stores/{id}` - Get store by ID
- `PUT /api/stores/{id}` - Update store
- `DELETE /api/stores/{id}` - Delete store

### Items
- `GET /api/items` - List all items (filter by `?store_id=` or `?section=`)
- `POST /api/items` - Create an item with store associations
- `GET /api/items/{id}` - Get item with stores
- `PUT /api/items/{id}` - Update item
- `DELETE /api/items/{id}` - Delete item

### Grocery Items
- `GET /api/grocery-items?user_id={id}` - Get user's grocery list
- `GET /api/grocery-items?user_id={id}&store_id={id}` - Filter by store
- `POST /api/grocery-items` - Add item to grocery list
- `PUT /api/grocery-items/{id}` - Update grocery item
- `DELETE /api/grocery-items/{id}` - Remove from list

### Templates
- `GET /api/grocery-templates?user_id={id}` - List user's templates
- `POST /api/grocery-templates` - Create template
- `GET /api/grocery-templates/{id}` - Get template with items
- `PUT /api/grocery-templates/{id}` - Update template
- `DELETE /api/grocery-templates/{id}` - Delete template
- `POST /api/grocery-templates/{id}/items` - Add item to template
- `DELETE /api/grocery-templates/{id}/items/{item_id}` - Remove item from template
- `POST /api/grocery-templates/{id}/apply?user_id={id}` - Apply template to grocery list

### Appointments
- `GET /api/appointments` - List appointments (filter by `?user_id=`)
- `POST /api/appointments` - Create appointment
- `GET /api/appointments/{id}` - Get appointment
- `PUT /api/appointments/{id}` - Update appointment
- `DELETE /api/appointments/{id}` - Delete appointment

### Tasks
- `GET /api/tasks` - List tasks (filter by `?assigned_to=` or `?category=`)
- `POST /api/tasks` - Create task
- `GET /api/tasks/{id}` - Get task
- `PUT /api/tasks/{id}` - Update task
- `DELETE /api/tasks/{id}` - Delete task

## Design Principles

1. **Database as Source of Truth**: SQLite database with well-defined schema
2. **Items as First-Class Objects**: Items have properties (quantity, section, stores)
3. **Stores as First-Class Objects**: Normalized store entities for extensibility
4. **Section Belongs to Item**: Grocery sections defined at item level for consistency
5. **Flexible Quantities**: String-based quantities allow "1 lb", "2-3 packages", etc.

## Testing

Visit http://localhost:3000/docs for interactive API documentation where you can test all endpoints.

## Using the Web Interface

### Main Interface (/)

Navigate between sections using the top navigation bar:

1. **Tasks**: Add and manage household tasks
   - Enter task title and select category
   - Mark tasks as complete
   - View by category and due date

2. **Appointments**: Schedule and track appointments
   - Add title, date/time, type, and patient/client name
   - Patient name prominently displayed (e.g., "Checkup - Will" or "Vet visit - Fluffy")
   - Associate with providers (medical, dental, vet)
   - Click provider name to view contact details in modal (phone, email, address)
   - View in list or calendar format

3. **Calendar**: Visual calendar view of all appointments
   - Month, week, and day views
   - Click events for details

4. **Grocery List**: Manage your shopping list
   - Select items from dropdown (sorted alphabetically)
   - Quantities auto-fill with defaults
   - Filter by store (e.g., "only Trader Joe's items")
   - Mark items as purchased
   - Save lists as templates

5. **Weather**: Weather information (coming soon)

### Admin Panel (/admin.html)

Access via the ⚙️ settings icon in the header → "Admin Panel"

1. **Stores**: Add/remove grocery stores
2. **Items**: Manage your item catalog
   - Set default quantities and sections
   - Assign items to specific stores
3. **Providers**: Track medical/dental/vet provider contact info
4. **Templates**: View and delete saved grocery list templates

## Future Enhancements

- User authentication and profiles
- Web search, trivia, weather integration
- Philips Hue light control
- Multi-household support
- AWS deployment with docker-compose

## License

Personal project - not currently licensed for distribution.