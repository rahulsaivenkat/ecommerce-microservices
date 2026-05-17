from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID, uuid4
import hmac, hashlib, json

from app.core.database import get_db
from app.core.config import get_settings
from app.dependencies import get_current_user
from app.publisher import publish_event
from app.models import Transaction, PaymentLog
from app.schemas import CreateOrderRequest, CreateOrderResponse, TransactionResponse

router = APIRouter(prefix="/api/v1/payment", tags=["payment"])


@router.post("/create-order", response_model=CreateOrderResponse)
async def create_payment_order(
    body: CreateOrderRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    settings = get_settings()
    user_id = current_user["user_id"]

    result = await db.execute(
        select(Transaction).filter(Transaction.order_id == body.order_id)
    )
    existing = result.scalars().first()
    if existing and existing.status == "SUCCESS":
        raise HTTPException(status_code=400, detail="Order already paid")

    fake_razorpay_order_id = f"order_stub_{uuid4().hex[:16]}"

    transaction = Transaction(
        order_id=body.order_id,
        user_id=UUID(user_id),
        razorpay_order_id=fake_razorpay_order_id,
        amount=body.amount,
        currency="INR",
        status="CREATED",
    )
    db.add(transaction)
    await db.commit()
    await db.refresh(transaction)

    return CreateOrderResponse(
        razorpay_order_id=fake_razorpay_order_id,
        razorpay_key_id=settings.RAZORPAY_KEY_ID,
        amount=float(body.amount),
        currency="INR",
        transaction_id=transaction.id,
    )


@router.post("/webhook")
async def razorpay_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    settings = get_settings()
    body_bytes = await request.body()
    signature = request.headers.get("X-Razorpay-Signature", "")

    expected = hmac.new(
        settings.RAZORPAY_WEBHOOK_SECRET.encode(),
        body_bytes,
        hashlib.sha256,
    ).hexdigest()

    if not hmac.compare_digest(expected, signature):
        raise HTTPException(status_code=400, detail="Invalid signature")

    payload = json.loads(body_bytes)
    event = payload.get("event", "")

    razorpay_order_id = (
        payload.get("payload", {})
        .get("payment", {})
        .get("entity", {})
        .get("order_id")
    )
    razorpay_payment_id = (
        payload.get("payload", {})
        .get("payment", {})
        .get("entity", {})
        .get("id")
    )

    if not razorpay_order_id:
        return {"status": "ignored"}

    result = await db.execute(
        select(Transaction).filter(Transaction.razorpay_order_id == razorpay_order_id)
    )
    transaction = result.scalars().first()
    if not transaction:
        return {"status": "transaction not found"}

    db.add(PaymentLog(
        transaction_id=transaction.id,
        event_type=event,
        payload=payload,
    ))

    if event == "payment.captured":
        transaction.status = "SUCCESS"
        transaction.razorpay_payment_id = razorpay_payment_id
        await db.commit()
        await publish_event("payment.success", {
            "order_id": str(transaction.order_id),
            "user_id": str(transaction.user_id),
            "amount": float(transaction.amount),
            "transaction_id": str(transaction.id),
        })

    elif event == "payment.failed":
        transaction.status = "FAILED"
        await db.commit()
        await publish_event("payment.failed", {
            "order_id": str(transaction.order_id),
            "user_id": str(transaction.user_id),
        })

    else:
        await db.commit()

    return {"status": "ok"}


@router.post("/webhook/test-success")
async def test_payment_success(
    body: dict,
    db: AsyncSession = Depends(get_db),
):
    razorpay_order_id = body.get("razorpay_order_id")
    if not razorpay_order_id:
        raise HTTPException(status_code=400, detail="razorpay_order_id required")

    result = await db.execute(
        select(Transaction).filter(Transaction.razorpay_order_id == razorpay_order_id)
    )
    transaction = result.scalars().first()
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")

    transaction.status = "SUCCESS"
    transaction.razorpay_payment_id = f"pay_stub_{uuid4().hex[:16]}"
    await db.commit()

    await publish_event("payment.success", {
        "order_id": str(transaction.order_id),
        "user_id": str(transaction.user_id),
        "amount": float(transaction.amount),
        "transaction_id": str(transaction.id),
    })
    return {"status": "success simulated", "transaction_id": str(transaction.id)}


@router.get("/status/{order_id}", response_model=TransactionResponse)
async def get_payment_status(
    order_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Transaction).filter(Transaction.order_id == UUID(order_id))
    )
    transaction = result.scalars().first()
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return TransactionResponse.model_validate(transaction)