from fastapi import APIRouter, Depends, HTTPException, Query, status, Request
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.cache import RedisCache, get_redis_cache
from app.schemas import ProductCreate, ProductResponse, ProductUpdate, InventoryResponse, InventoryUpdate
from app.models import Product, Inventory
from app.dependencies import get_current_user
from typing import Optional
import hashlib
import json
from uuid import UUID

router = APIRouter(prefix="/api/v1/products", tags=["products"])

@router.get("/", response_model=list[ProductResponse])
async def get_products(
    page: Optional[int] = Query(None),
    limit: Optional[int] = Query(None),
    category_id: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    cache: RedisCache = Depends(get_redis_cache),
):
    query_params = {"page": page, "limit": limit, "category_id": category_id, "search": search}
    query_hash = hashlib.sha256(json.dumps(query_params, sort_keys=True).encode()).hexdigest()
    cache_key = f"products:list:{query_hash}"
    cached_products = await cache.get(cache_key)
    if cached_products is not None:
        return [ProductResponse.model_validate(p) for p in cached_products]

    stmt = select(Product).filter(Product.is_active == True)
    if category_id is not None:
        stmt = stmt.filter(Product.category_id == UUID(category_id))
    if search is not None:
        stmt = stmt.filter(Product.name.ilike(f"%{search}%"))
    
    if page is not None and limit is not None:
        stmt = stmt.offset(page * limit)
    if limit is not None:
        stmt = stmt.limit(limit)

    result = await db.execute(stmt)
    products = result.scalars().all()
    products_response = [ProductResponse.model_validate(product) for product in products]
    await cache.set(cache_key, [p.model_dump(mode='json') for p in products_response], ttl=120)
    return products_response

@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(
    product_id: str,
    db: AsyncSession = Depends(get_db),
    cache: RedisCache = Depends(get_redis_cache),
):
    cache_key = f"product:{product_id}"
    cached_product = await cache.get(cache_key)
    if cached_product is not None:
        return ProductResponse.model_validate(cached_product)

    result = await db.execute(select(Product).filter(Product.id == UUID(product_id)))
    product = result.scalars().first()
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    product_response = ProductResponse.model_validate(product)
    await cache.set(cache_key, product_response.model_dump(mode='json'), ttl=300)
    return product_response

@router.post("/", status_code=status.HTTP_201_CREATED, response_model=ProductResponse)
async def create_product(
    product: ProductCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    cache: RedisCache = Depends(get_redis_cache),
):
    user_role = (await get_current_user(request))["role"]
    if user_role not in ["vendor", "admin"]:
        raise HTTPException(status_code=403, detail="Forbidden")
    db_product = Product(**product.model_dump(exclude_unset=True))
    db.add(db_product)
    await db.commit()
    await db.refresh(db_product)
    inventory = Inventory(product_id=db_product.id)
    db.add(inventory)
    await db.commit()
    await cache.delete_pattern("products:list:*")
    return ProductResponse.model_validate(db_product)

@router.put("/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: str,
    product: ProductUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    cache: RedisCache = Depends(get_redis_cache),
):
    user_role = (await get_current_user(request))["role"]
    if user_role not in ["vendor", "admin"]:
        raise HTTPException(status_code=403, detail="Forbidden")
    result = await db.execute(select(Product).filter(Product.id == UUID(product_id)))
    db_product = result.scalars().first()
    if db_product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    for key, value in product.model_dump(exclude_unset=True).items():
        setattr(db_product, key, value)
    await db.commit()
    await db.refresh(db_product)
    await cache.delete(f"product:{product_id}")
    await cache.delete_pattern("products:list:*")
    return ProductResponse.model_validate(db_product)

@router.delete("/{product_id}")
async def delete_product(
    product_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    cache: RedisCache = Depends(get_redis_cache),
):
    user_role = (await get_current_user(request))["role"]
    if user_role not in ["vendor", "admin"]:
        raise HTTPException(status_code=403, detail="Forbidden")
    result = await db.execute(select(Product).filter(Product.id == UUID(product_id)))
    db_product = result.scalars().first()
    if db_product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    db_product.is_active = False
    await db.commit()
    await cache.delete(f"product:{product_id}")
    await cache.delete_pattern("products:list:*")
    return JSONResponse(status_code=200, content={"message": "Product deleted"})

@router.get("/{product_id}/inventory", response_model=InventoryResponse)
async def get_inventory(
    product_id: str,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Inventory).filter(Inventory.product_id == UUID(product_id)))
    inventory = result.scalars().first()
    if inventory is None:
        raise HTTPException(status_code=404, detail="Inventory not found")
    return InventoryResponse.model_validate(inventory)

@router.put("/{product_id}/inventory", response_model=InventoryResponse)
async def update_inventory(
    product_id: str,
    inventory: InventoryUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    user_role = (await get_current_user(request))["role"]
    if user_role not in ["vendor", "admin"]:
        raise HTTPException(status_code=403, detail="Forbidden")
    result = await db.execute(select(Inventory).filter(Inventory.product_id == UUID(product_id)))
    db_inventory = result.scalars().first()
    if db_inventory is None:
        raise HTTPException(status_code=404, detail="Inventory not found")
    db_inventory.quantity = inventory.quantity
    await db.commit()
    await db.refresh(db_inventory)
    return InventoryResponse.model_validate(db_inventory)
