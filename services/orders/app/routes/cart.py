from fastapi import APIRouter, Depends, HTTPException, status
from httpx import AsyncClient
from typing import List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.core.database import get_db
from app.core.config import get_settings
from app.dependencies import get_current_user
import app.models as models
import app.schemas as schemas

router = APIRouter(prefix="/api/v1/cart")

@router.get("/", response_model=schemas.CartResponse)
async def get_cart(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    user_id = current_user["user_id"]
    result = await db.execute(select(models.Cart).filter(models.Cart.user_id == UUID(user_id)))
    cart = result.scalars().first()
    if not cart:
        cart = models.Cart(user_id=UUID(user_id))
        db.add(cart)
        await db.commit()
        await db.refresh(cart)
    result = await db.execute(select(models.CartItem).filter(models.CartItem.cart_id == cart.id))
    cart_items = result.scalars().all()
    total = sum(item.unit_price * item.quantity for item in cart_items)
    return schemas.CartResponse(
        id=cart.id,
        user_id=cart.user_id,
        items=[schemas.CartItemResponse(id=item.id, cart_id=item.cart_id, product_id=item.product_id, product_name=item.product_name, unit_price=item.unit_price, quantity=item.quantity, added_at=item.added_at) for item in cart_items],
        total=float(total),
    )

@router.post("/items", response_model=schemas.CartItemResponse)
async def add_item_to_cart(
    item: schemas.CartItemAdd,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    user_id = current_user["user_id"]
    products_url = get_settings().PRODUCTS_SERVICE_URL
    async with AsyncClient() as http_client:
        product_response = await http_client.get(f"{products_url}/api/v1/products/{item.product_id}")
    if product_response.status_code != 200:
        raise HTTPException(status_code=404, detail="Product not found")
    product_data = product_response.json()
    result = await db.execute(select(models.Cart).filter(models.Cart.user_id == UUID(user_id)))
    cart = result.scalars().first()
    if not cart:
        cart = models.Cart(user_id=UUID(user_id))
        db.add(cart)
        await db.commit()
        await db.refresh(cart)
    result = await db.execute(select(models.CartItem).filter(models.CartItem.cart_id == cart.id, models.CartItem.product_id == UUID(str(item.product_id))))
    cart_item = result.scalars().first()
    if cart_item:
        cart_item.quantity += item.quantity
    else:
        cart_item = models.CartItem(cart_id=cart.id, product_id=UUID(str(item.product_id)), product_name=product_data["name"], unit_price=product_data["price"], quantity=item.quantity)
        db.add(cart_item)
    await db.commit()
    await db.refresh(cart_item)
    return schemas.CartItemResponse(id=cart_item.id, cart_id=cart_item.cart_id, product_id=cart_item.product_id, product_name=cart_item.product_name, unit_price=cart_item.unit_price, quantity=cart_item.quantity, added_at=cart_item.added_at)

@router.put("/items/{item_id}", response_model=schemas.CartItemResponse)
async def update_item_in_cart(
    item_id: str,
    item: schemas.CartItemUpdate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    user_id = current_user["user_id"]
    result = await db.execute(select(models.CartItem).filter(models.CartItem.id == UUID(item_id)))
    cart_item = result.scalars().first()
    if not cart_item:
        raise HTTPException(status_code=404, detail="Item not found")
    result = await db.execute(select(models.Cart).filter(models.Cart.id == cart_item.cart_id))
    cart = result.scalars().first()
    if not cart or str(cart.user_id) != user_id:
        raise HTTPException(status_code=403, detail="Forbidden")
    cart_item.quantity = item.quantity
    await db.commit()
    await db.refresh(cart_item)
    return schemas.CartItemResponse(id=cart_item.id, cart_id=cart_item.cart_id, product_id=cart_item.product_id, product_name=cart_item.product_name, unit_price=cart_item.unit_price, quantity=cart_item.quantity, added_at=cart_item.added_at)

@router.delete("/items/{item_id}", status_code=status.HTTP_200_OK)
async def delete_item_from_cart(
    item_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    user_id = current_user["user_id"]
    result = await db.execute(select(models.CartItem).filter(models.CartItem.id == UUID(item_id)))
    cart_item = result.scalars().first()
    if not cart_item:
        raise HTTPException(status_code=404, detail="Item not found")
    result = await db.execute(select(models.Cart).filter(models.Cart.id == cart_item.cart_id))
    cart = result.scalars().first()
    if not cart or str(cart.user_id) != user_id:
        raise HTTPException(status_code=403, detail="Forbidden")
    await db.delete(cart_item)
    await db.commit()
    return {"message": "Item removed"}