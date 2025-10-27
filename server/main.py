"""
Main FastAPI application for the Household AI Assistant.

This is the entry point for the server. It sets up all routes and middleware.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routers import (
    stores, items, grocery_items, templates,
    providers, appointments, tasks
)
from .database import DATABASE_PATH


# Create FastAPI application
app = FastAPI(
    title="Household AI Assistant API",
    description=(
        "API for managing household tasks, groceries, "
        "appointments, and more"
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS for browser access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include all routers
app.include_router(stores.router)
app.include_router(items.router)
app.include_router(grocery_items.router)
app.include_router(templates.router)
app.include_router(providers.router)
app.include_router(appointments.router)
app.include_router(tasks.router)


@app.get("/")
def root():
    """Root endpoint with API information."""
    return {
        "name": "Household AI Assistant API",
        "version": "1.0.0",
        "docs": "/docs",
        "database": str(DATABASE_PATH),
        "endpoints": {
            "stores": "/api/stores",
            "items": "/api/items",
            "grocery_items": "/api/grocery-items",
            "templates": "/api/grocery-templates",
            "providers": "/api/providers",
            "appointments": "/api/appointments",
            "tasks": "/api/tasks"
        }
    }


@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3000)