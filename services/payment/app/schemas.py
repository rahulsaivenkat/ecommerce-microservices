from pydantic import BaseModel, ConfigDict
from typing import Optional
from uuid import UUID
from datetime import datetime
from decimal import Decimal

class CreateOrderRequest(BaseModel):
    order_id: UUID
    amount: Decimal

class CreateOrderResponse(BaseModel):
    razorpay_order_id: str
    razorpay_key_id: str
    amount: float
    currency: str
    transaction_id: UUID

class TransactionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    order_id: UUID
    user_id: UUID
    razorpay_order_id: Optional[str] = None
    razorpay_payment_id: Optional[str] = None
    amount: float
    currency: str
    status: str
    created_at: datetime