from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional
from uuid import UUID

class CategoryCreate(BaseModel):
    name: str
    slug: str

class CategoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    name: str
    slug: str
    created_at: datetime

class ProductCreate(BaseModel):
    name: str
    description: Optional[str] = None
    price: float
    sku: str
    category_id: Optional[UUID] = None
    vendor_id: Optional[UUID] = None

class ProductResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    name: str
    description: Optional[str] = None
    price: float
    sku: str
    is_active: bool
    category_id: Optional[UUID] = None
    vendor_id: Optional[UUID] = None
    created_at: datetime

class ProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    category_id: Optional[UUID] = None
    is_active: Optional[bool] = None

class InventoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    product_id: UUID
    quantity: int
    low_stock_threshold: int

class InventoryUpdate(BaseModel):
    quantity: int
