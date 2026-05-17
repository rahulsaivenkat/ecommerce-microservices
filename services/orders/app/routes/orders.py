from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Query
from typing import List, Optional
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from asyncio import sleep

from app.core.database import get_db, SessionLocal
from app.dependencies import get_current_user
from app.publisher import publish_event
import app.models as models
import app.schemas as schemas

router = APIRouter(prefix="/api/v1/orders")


async def _auto_cancel_order_task(order_id: str, user_id: str):
    await sleep(900)
    async with SessionLocal() as db_session:                          # BUG 13 FIXED
        try:
            result = await db_session.execute(
                select(models.Order).filter(models.Order.id == UUID(order_id))
            )
            order = result.scalars().first()
            if order and order.status in ["PENDING", "CONFIRMED"]:
                old_status = order.status
                order.status = "CANCELLED"
                db_session.add(order)
                db_session.add(models.OrderStatusHistory(
                    order_id=order.id,
                    old_status=old_status,
                    new_status="CANCELLED",
                ))
                await db_session.commit()
                await publish_event("order.cancelled", {
                    "order_id": str(order.id),
                    "user_id": user_id,
                })
        except Exception as e:
            print(f"Error in auto_cancel_order_task for order {order_id}: {e}")


@router.post("/", response_model=schemas.OrderResponse, status_code=status.HTTP_201_CREATED)
async def create_order(
    background_tasks: BackgroundTasks,                                # BUG 10 FIXED
    current_user: dict = Depends(get_current_user),                  # BUG 11 FIXED
    db: AsyncSession = Depends(get_db),                              # BUG 12 FIXED
):
    user_id = current_user["user_id"]                                # BUG 11 FIXED

    result = await db.execute(                                       # BUG 9 FIXED
        select(models.Cart).filter(models.Cart.user_id == UUID(user_id))
    )
    cart = result.scalars().first()
    if not cart:
        raise HTTPException(status_code=400, detail="Cart is empty")

    result = await db.execute(
        select(models.CartItem).filter(models.CartItem.cart_id == cart.id)
    )
    cart_items = result.scalars().all()
    if not cart_items:
        raise HTTPException(status_code=400, detail="Cart is empty")

    total_amount = sum(item.unit_price * item.quantity for item in cart_items)

    order = models.Order(user_id=UUID(user_id), total_amount=total_amount, status="PENDING")
    db.add(order)
    await db.commit()
    await db.refresh(order)

    for item in cart_items:
        db.add(models.OrderItem(
            order_id=order.id,
            product_id=item.product_id,
            product_name=item.product_name,
            quantity=item.quantity,
            unit_price=item.unit_price,
            subtotal=item.unit_price * item.quantity,
        ))

    await db.commit()

    for item in cart_items:
        await db.delete(item)

    await db.commit()

    await db.delete(cart)
    await db.commit()

    await publish_event("order.created", {
        "order_id": str(order.id),
        "user_id": user_id,
        "total_amount": float(total_amount),                         # BUG 16 FIXED
    })

    background_tasks.add_task(_auto_cancel_order_task, str(order.id), user_id)

    result = await db.execute(
        select(models.OrderItem).filter(models.OrderItem.order_id == order.id)
    )
    order_items = result.scalars().all()                             # BUG 15 FIXED

    return schemas.OrderResponse(
        id=order.id,
        user_id=order.user_id,
        status=order.status,
        total_amount=order.total_amount,
        items=[schemas.OrderItemResponse(
            id=item.id,
            order_id=item.order_id,
            product_id=item.product_id,
            product_name=item.product_name,
            quantity=item.quantity,
            unit_price=item.unit_price,
            subtotal=item.subtotal,
        ) for item in order_items],
    )


@router.get("/", response_model=List[schemas.OrderResponse])
async def get_orders(
    current_user: dict = Depends(get_current_user),                  # BUG 11 FIXED
    db: AsyncSession = Depends(get_db),                              # BUG 12 FIXED
    page: Optional[int] = Query(1, ge=1),
    limit: Optional[int] = Query(10, ge=1, le=100),
):
    user_id = current_user["user_id"]
    offset = (page - 1) * limit

    result = await db.execute(                                       # BUG 9 FIXED
        select(models.Order)
        .filter(models.Order.user_id == UUID(user_id))
        .order_by(desc(models.Order.created_at))
        .offset(offset).limit(limit)
    )
    orders = result.scalars().all()

    response_orders = []
    for order in orders:
        items_result = await db.execute(
            select(models.OrderItem).filter(models.OrderItem.order_id == order.id)
        )
        order_items = items_result.scalars().all()
        response_orders.append(schemas.OrderResponse(
            id=order.id,
            user_id=order.user_id,
            status=order.status,
            total_amount=order.total_amount,
            items=[schemas.OrderItemResponse(
                id=item.id,
                order_id=item.order_id,
                product_id=item.product_id,
                product_name=item.product_name,
                quantity=item.quantity,
                unit_price=item.unit_price,
                subtotal=item.subtotal,
            ) for item in order_items],
        ))
    return response_orders


@router.get("/{order_id}", response_model=schemas.OrderResponse)
async def get_order(                                                  # BUG 14 FIXED: removed duplicate
    order_id: str,
    current_user: dict = Depends(get_current_user),                  # BUG 11 FIXED
    db: AsyncSession = Depends(get_db),                              # BUG 12 FIXED
):
    user_id = current_user["user_id"]
    result = await db.execute(                                       # BUG 9 FIXED
        select(models.Order).filter(models.Order.id == UUID(order_id))
    )
    order = result.scalars().first()
    if not order or str(order.user_id) != user_id:
        raise HTTPException(status_code=404, detail="Order not found")

    items_result = await db.execute(
        select(models.OrderItem).filter(models.OrderItem.order_id == order.id)
    )
    order_items = items_result.scalars().all()

    return schemas.OrderResponse(
        id=order.id,
        user_id=order.user_id,
        status=order.status,
        total_amount=order.total_amount,
        items=[schemas.OrderItemResponse(
            id=item.id,
            order_id=item.order_id,
            product_id=item.product_id,
            product_name=item.product_name,
            quantity=item.quantity,
            unit_price=item.unit_price,
            subtotal=item.subtotal,
        ) for item in order_items],
    )


@router.put("/{order_id}/cancel", response_model=schemas.OrderResponse)
async def cancel_order(
    order_id: str,
    current_user: dict = Depends(get_current_user),                  # BUG 11 FIXED
    db: AsyncSession = Depends(get_db),                              # BUG 12 FIXED
):
    user_id = current_user["user_id"]
    result = await db.execute(                                       # BUG 9 FIXED
        select(models.Order).filter(models.Order.id == UUID(order_id))
    )
    order = result.scalars().first()
    if not order or str(order.user_id) != user_id:
        raise HTTPException(status_code=404, detail="Order not found")
    if order.status not in ["PENDING", "CONFIRMED"]:
        raise HTTPException(status_code=400, detail="Order cannot be cancelled")

    old_status = order.status
    order.status = "CANCELLED"
    db.add(models.OrderStatusHistory(
        order_id=order.id,
        old_status=old_status,
        new_status="CANCELLED",
    ))
    await db.commit()
    await db.refresh(order)

    await publish_event("order.cancelled", {
        "order_id": str(order.id),
        "user_id": user_id,
    })

    items_result = await db.execute(
        select(models.OrderItem).filter(models.OrderItem.order_id == order.id)
    )
    order_items = items_result.scalars().all()

    return schemas.OrderResponse(
        id=order.id,
        user_id=order.user_id,
        status=order.status,
        total_amount=order.total_amount,
        items=[schemas.OrderItemResponse(
            id=item.id,
            order_id=item.order_id,
            product_id=item.product_id,
            product_name=item.product_name,
            quantity=item.quantity,
            unit_price=item.unit_price,
            subtotal=item.subtotal,
        ) for item in order_items],
    )