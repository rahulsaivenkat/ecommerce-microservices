from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime
from typing import Optional, List, Dict


class CartItemAdd(BaseModel):
    product_id: UUID
    quantity: int = 1

class CartItemUpdate(BaseModel):
    quantity: int

class CartItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    cart_id: UUID
    product_id: UUID
    product_name: str
    unit_price: float
    quantity: int
    added_at: Optional[datetime] = None

class CartResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    user_id: UUID
    items: List[CartItemResponse] = []
    total: float = 0

class OrderCreate(BaseModel):
    shipping_address: Optional[Dict] = None

class OrderItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    order_id: Optional[UUID] = None
    product_id: UUID
    product_name: str
    quantity: int
    unit_price: float
    subtotal: float

class OrderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    user_id: UUID
    status: str
    total_amount: float
    shipping_address: Optional[dict] = None
    payment_id: Optional[UUID] = None
    created_at: Optional[datetime] = None
    items: List[OrderItemResponse] = []

class OrderStatusHistoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    order_id: UUID
    old_status: Optional[str] = None
    new_status: str
    changed_at: Optional[datetime] = None