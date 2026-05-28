"""
#
"""
import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.models import SubcontractorProduct, SubcontractorCard, Product
from app.schemas.subcontractor_product import (
    SubcontractorProductCreate,
    SubcontractorProductUpdate,
    SubcontractorProductResponse
)

router = APIRouter()


def _parse_uuid(value: str, field_name: str) -> uuid.UUID:
    try:
        return value if isinstance(value, uuid.UUID) else uuid.UUID(str(value))
    except (ValueError, TypeError):
        raise HTTPException(status_code=400, detail=f"Invalid {field_name}")


@router.get("/subcontractor/{subcontractor_id}", response_model=List[SubcontractorProductResponse])
async def get_subcontractor_products(
    subcontractor_id: str,
    db: AsyncSession = Depends(get_db)
):
    try:
        items = await SubcontractorProduct.get_by_subcontractor_card(db, subcontractor_id)
        return items
    except Exception as e:
        print(f"Error getting subcontractor products for {subcontractor_id}: {e}")
        return []


@router.post("/", response_model=SubcontractorProductResponse)
async def add_product_to_subcontractor(
    item: SubcontractorProductCreate,
    db: AsyncSession = Depends(get_db)
):
    try:
        card = await SubcontractorCard.get_by_id(db, item.subcontractor_card_id)
        if not card:
            raise HTTPException(status_code=404, detail="Subcontractor card not found")

        product = await Product.get_by_id(db, item.product_id)
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")

        item_data = item.dict()
        if not item_data.get("unit"):
            item_data["unit"] = getattr(product, "unit", None) or "pcs"

        if item_data.get("custom_price") is not None:
            item_data["unit_price"] = item_data["custom_price"]

        db_item = await SubcontractorProduct.create(db, **item_data)
        return db_item
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error creating subcontractor product: {e}")
        raise HTTPException(status_code=404, detail="Product not found")


@router.get("/{item_id}", response_model=SubcontractorProductResponse)
async def get_subcontractor_product(
    item_id: str,
    db: AsyncSession = Depends(get_db)
):
    item = await SubcontractorProduct.get_by_id(db, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Product not found")
    return item


@router.put("/{item_id}", response_model=SubcontractorProductResponse)
async def update_subcontractor_product(
    item_id: str,
    item_update: SubcontractorProductUpdate,
    db: AsyncSession = Depends(get_db)
):
    try:
        updated = await SubcontractorProduct.update(db, item_id, **item_update.dict(exclude_unset=True))
        if not updated:
            raise HTTPException(status_code=404, detail="Product not found")
        return updated
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error updating subcontractor product {item_id}: {e}")
        raise HTTPException(status_code=400, detail="Failed to update product")


@router.delete("/{item_id}")
async def delete_subcontractor_product(
    item_id: str,
    db: AsyncSession = Depends(get_db)
):
    success = await SubcontractorProduct.delete(db, item_id)
    if not success:
        raise HTTPException(status_code=404, detail="Product not found")
    return {"message": "Product deleted"}
