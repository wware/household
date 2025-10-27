"""
Pydantic models for the Household AI Assistant API.

These models define the shape of data for API requests and responses,
with strong typing and validation.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, EmailStr


# =============================================================================
# Users
# =============================================================================

class UserBase(BaseModel):
    """Base user model with shared fields."""
    name: str = Field(..., description="User's display name")
    email: EmailStr = Field(..., description="User's email address")


class UserCreate(UserBase):
    """Model for creating a new user."""
    pass


class UserUpdate(BaseModel):
    """Model for updating a user."""
    name: Optional[str] = Field(None, description="User's display name")
    email: Optional[EmailStr] = Field(None, description="User's email address")


class User(UserBase):
    """Complete user model with database fields."""
    id: int = Field(..., description="User ID")
    created_at: datetime = Field(..., description="Creation timestamp")

    class Config:
        from_attributes = True


# =============================================================================
# Stores
# =============================================================================

class StoreBase(BaseModel):
    """Base store model with shared fields."""
    name: str = Field(..., description="Store name (e.g., 'TraderJoes', 'WholeFoods')")


class StoreCreate(StoreBase):
    """Model for creating a new store."""
    pass


class StoreUpdate(BaseModel):
    """Model for updating a store."""
    name: Optional[str] = Field(None, description="Store name")


class Store(StoreBase):
    """Complete store model with database fields."""
    id: int = Field(..., description="Store ID")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    class Config:
        from_attributes = True


# =============================================================================
# Items
# =============================================================================

class ItemBase(BaseModel):
    """Base item model with shared fields."""
    name: str = Field(..., description="Item name (e.g., 'Butter', 'English muffins')")
    default_quantity: Optional[str] = Field(None, description="Default quantity (e.g., '1 lb', '2 packages')")
    quantity_is_int: bool = Field(False, description="True if quantity is naturally an integer")
    section: Optional[str] = Field(None, description="Grocery section: Meat, Dairy, Produce, Freezer, Breads, Other")


class ItemCreate(ItemBase):
    """Model for creating a new item."""
    store_ids: list[int] = Field(default_factory=list, description="List of store IDs where this item is available")


class ItemUpdate(BaseModel):
    """Model for updating an item."""
    name: Optional[str] = Field(None, description="Item name")
    default_quantity: Optional[str] = Field(None, description="Default quantity")
    quantity_is_int: Optional[bool] = Field(None, description="True if quantity is naturally an integer")
    section: Optional[str] = Field(None, description="Grocery section")
    store_ids: Optional[list[int]] = Field(None, description="List of store IDs where this item is available")


class Item(ItemBase):
    """Complete item model with database fields."""
    id: int = Field(..., description="Item ID")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    class Config:
        from_attributes = True


class ItemWithStores(Item):
    """Item model with associated stores."""
    stores: list[Store] = Field(default_factory=list, description="Stores where this item is available")


# =============================================================================
# Grocery Items
# =============================================================================

class GroceryItemBase(BaseModel):
    """Base grocery item model with shared fields."""
    item_id: int = Field(..., description="Reference to the item definition")
    quantity: Optional[str] = Field(None, description="Quantity override (uses item default if not specified)")
    int_quantity: Optional[int] = Field(None, description="Parsed integer quantity when applicable")


class GroceryItemCreate(GroceryItemBase):
    """Model for creating a new grocery item."""
    user_id: int = Field(..., description="User who added this item to their list")


class GroceryItemUpdate(BaseModel):
    """Model for updating a grocery item."""
    quantity: Optional[str] = Field(None, description="Quantity override")
    int_quantity: Optional[int] = Field(None, description="Parsed integer quantity")
    purchased: Optional[bool] = Field(None, description="Whether the item has been purchased")


class GroceryItem(GroceryItemBase):
    """Complete grocery item model with database fields."""
    id: int = Field(..., description="Grocery item ID")
    purchased: bool = Field(..., description="Whether the item has been purchased")
    user_id: int = Field(..., description="User who owns this grocery item")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    class Config:
        from_attributes = True


class GroceryItemWithDetails(GroceryItem):
    """Grocery item with full item details and stores."""
    item: ItemWithStores = Field(..., description="Full item details including stores")


# =============================================================================
# Grocery Templates
# =============================================================================

class GroceryTemplateBase(BaseModel):
    """Base grocery template model with shared fields."""
    name: str = Field(..., description="Template name (e.g., 'Weekly Groceries', 'Pet Supplies')")
    is_default: bool = Field(False, description="Whether this is the default template for the user")


class GroceryTemplateCreate(GroceryTemplateBase):
    """Model for creating a new grocery template."""
    user_id: int = Field(..., description="User who owns this template")


class GroceryTemplateUpdate(BaseModel):
    """Model for updating a grocery template."""
    name: Optional[str] = Field(None, description="Template name")
    is_default: Optional[bool] = Field(None, description="Whether this is the default template")


class GroceryTemplate(GroceryTemplateBase):
    """Complete grocery template model with database fields."""
    id: int = Field(..., description="Template ID")
    user_id: int = Field(..., description="User who owns this template")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    class Config:
        from_attributes = True


# =============================================================================
# Grocery Template Items
# =============================================================================

class GroceryTemplateItemBase(BaseModel):
    """Base grocery template item model with shared fields."""
    item_id: int = Field(..., description="Reference to the item definition")
    quantity: Optional[str] = Field(None, description="Quantity override (uses item default if not specified)")


class GroceryTemplateItemCreate(GroceryTemplateItemBase):
    """Model for creating a new grocery template item."""
    template_id: int = Field(..., description="Template this item belongs to")


class GroceryTemplateItem(GroceryTemplateItemBase):
    """Complete grocery template item model with database fields."""
    id: int = Field(..., description="Template item ID")
    template_id: int = Field(..., description="Template this item belongs to")
    created_at: datetime = Field(..., description="Creation timestamp")

    class Config:
        from_attributes = True


class GroceryTemplateItemWithDetails(GroceryTemplateItem):
    """Template item with full item details."""
    item: ItemWithStores = Field(..., description="Full item details including stores")


class GroceryTemplateWithItems(GroceryTemplate):
    """Template with all its items."""
    items: list[GroceryTemplateItemWithDetails] = Field(default_factory=list, description="Items in this template")


# =============================================================================
# Providers (Doctors, Vets, Service Providers)
# =============================================================================

class ProviderBase(BaseModel):
    """Base provider model with shared fields."""
    name: str = Field(..., description="Provider name (e.g., 'Dr. Smith', 'Main Street Veterinary')")
    phone: Optional[str] = Field(None, description="Phone number")
    email: Optional[str] = Field(None, description="Email address")
    website: Optional[str] = Field(None, description="Website URL")
    address: Optional[str] = Field(None, description="Physical address (multi-line)")
    info: Optional[str] = Field(None, description="Free-form description/info field")


class ProviderCreate(ProviderBase):
    """Model for creating a new provider."""
    pass


class ProviderUpdate(BaseModel):
    """Model for updating a provider."""
    name: Optional[str] = Field(None, description="Provider name")
    phone: Optional[str] = Field(None, description="Phone number")
    email: Optional[str] = Field(None, description="Email address")
    website: Optional[str] = Field(None, description="Website URL")
    address: Optional[str] = Field(None, description="Physical address")
    info: Optional[str] = Field(None, description="Free-form description/info")


class Provider(ProviderBase):
    """Complete provider model with database fields."""
    id: int = Field(..., description="Provider ID")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    class Config:
        from_attributes = True


# =============================================================================
# Appointments
# =============================================================================

class AppointmentBase(BaseModel):
    """Base appointment model with shared fields."""
    title: str = Field(..., description="Appointment title")
    date: datetime = Field(..., description="Appointment date and time")
    type: str = Field(..., description="Appointment type: medical, pet, other")
    notes: Optional[str] = Field(None, description="Additional notes")
    provider_id: Optional[int] = Field(None, description="Provider ID (doctor, vet, etc.)")
    patient_name: Optional[str] = Field(None, description="Name of patient (user name or pet name)")


class AppointmentCreate(AppointmentBase):
    """Model for creating a new appointment."""
    created_by: int = Field(..., description="User who created this appointment")


class AppointmentUpdate(BaseModel):
    """Model for updating an appointment."""
    title: Optional[str] = Field(None, description="Appointment title")
    date: Optional[datetime] = Field(None, description="Appointment date and time")
    type: Optional[str] = Field(None, description="Appointment type")
    notes: Optional[str] = Field(None, description="Additional notes")
    provider_id: Optional[int] = Field(None, description="Provider ID")
    patient_name: Optional[str] = Field(None, description="Patient name")


class Appointment(AppointmentBase):
    """Complete appointment model with database fields."""
    id: int = Field(..., description="Appointment ID")
    created_by: int = Field(..., description="User who created this appointment")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    class Config:
        from_attributes = True


class AppointmentWithProvider(Appointment):
    """Appointment with provider details."""
    provider: Optional[Provider] = Field(None, description="Full provider details")


# =============================================================================
# Tasks
# =============================================================================

class TaskBase(BaseModel):
    """Base task model with shared fields."""
    title: str = Field(..., description="Task title")
    category: str = Field(..., description="Task category: household, pet, maintenance, travel, other")
    due_date: Optional[datetime] = Field(None, description="Task due date")
    assigned_to: Optional[int] = Field(None, description="User ID this task is assigned to")


class TaskCreate(TaskBase):
    """Model for creating a new task."""
    pass


class TaskUpdate(BaseModel):
    """Model for updating a task."""
    title: Optional[str] = Field(None, description="Task title")
    category: Optional[str] = Field(None, description="Task category")
    completed: Optional[bool] = Field(None, description="Whether the task is completed")
    due_date: Optional[datetime] = Field(None, description="Task due date")
    assigned_to: Optional[int] = Field(None, description="User ID this task is assigned to")


class Task(TaskBase):
    """Complete task model with database fields."""
    id: int = Field(..., description="Task ID")
    completed: bool = Field(..., description="Whether the task is completed")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    class Config:
        from_attributes = True