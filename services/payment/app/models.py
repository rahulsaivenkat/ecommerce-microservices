from app.core.database import Base
from sqlalchemy import Column, String, Numeric, DateTime, ForeignKey, JSON
from sqlalchemy import UUID
from uuid import uuid4
from datetime import datetime

class Transaction(Base):
    __tablename__ = "transactions"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    order_id = Column(UUID(as_uuid=True), unique=True, nullable=False)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    razorpay_order_id = Column(String, unique=True, nullable=True)
    razorpay_payment_id = Column(String, nullable=True)
    amount = Column(Numeric(10, 2), nullable=False)
    currency = Column(String, default="INR")
    status = Column(String, default="CREATED")
    created_at = Column(DateTime, default=lambda: datetime.utcnow())
    updated_at = Column(DateTime, default=lambda: datetime.utcnow(), onupdate=lambda: datetime.utcnow())

class PaymentLog(Base):
    __tablename__ = "payment_logs"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    transaction_id = Column(UUID(as_uuid=True), ForeignKey("transactions.id"), nullable=False)
    event_type = Column(String, nullable=False)
    payload = Column(JSON, nullable=True)
    logged_at = Column(DateTime, default=lambda: datetime.utcnow())