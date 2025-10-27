# Household AI Assistant

A shared AI assistant for household coordination, tracking groceries, appointments, tasks, and more.

## Features

- **Grocery Management**: Track items, organize by store and section, create reusable templates
- **Appointments**: Schedule medical, pet, and other appointments
- **Tasks**: Manage household tasks with categories and assignments
- **Multi-user**: Shared between household members with per-user preferences

## Project Structure

```
household/
├── schema.sql              # Database schema definition
├── DB_SCHEMA_DESIGN.md     # Database design documentation
├── requirements.txt        # Python dependencies
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

The server will be available at:
- API: http://localhost:3000
- Interactive docs: http://localhost:3000/docs
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

## Future Enhancements

- Multi-household support (each household has its own items)
- User authentication
- Web search, trivia, weather integration
- Philips Hue light control
- Client web interface (static HTML/JS/CSS)
- AWS deployment with docker-compose for prototyping

## License

Personal project - not currently licensed for distribution.