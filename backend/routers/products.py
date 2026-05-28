"""
Products API router.
"""
import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.models import ProductCategory, Product, DealProduct, Deal, Lead, LeadProduct, ContractDocument, ContractDocumentProductLink
from app.schemas.product_category import ProductCategoryCreate, ProductCategoryUpdate, ProductCategoryResponse
from app.schemas.product import ProductCreate, ProductUpdate, ProductResponse
from app.schemas.deal_product import DealProductCreate, DealProductUpdate, DealProductResponse
from app.schemas.lead_product import LeadProductCreate, LeadProductUpdate, LeadProductResponse

router = APIRouter()

def _parse_uuid(value: str, field_name: str) -> uuid.UUID:
    try:
        return value if isinstance(value, uuid.UUID) else uuid.UUID(str(value))
    except (ValueError, TypeError):
        raise HTTPException(status_code=400, detail=f"Invalid {field_name}")


async def _attach_invoice_links(db: AsyncSession, deal_products: List[DealProduct]) -> List[DealProduct]:
    if not deal_products:
        return deal_products
    product_ids = [str(item.id) for item in deal_products if getattr(item, "id", None)]
    for item in deal_products:
        setattr(item, "invoice_links", [])
    if not product_ids:
        return deal_products

    links_result = await db.execute(
        select(ContractDocumentProductLink)
        .where(ContractDocumentProductLink.deal_product_id.in_(product_ids))
    )
    links = links_result.scalars().all()
    if not links:
        return deal_products

    document_ids = []
    for link in links:
        try:
            document_ids.append(uuid.UUID(str(link.contract_document_id)))
        except (ValueError, TypeError):
            continue
    if not document_ids:
        return deal_products

    documents_result = await db.execute(
        select(ContractDocument)
        .where(ContractDocument.id.in_(document_ids))
        .where(ContractDocument.doc_type == "invoice")
        .order_by(ContractDocument.number_in_contract.asc())
    )
    documents_by_id = {str(document.id): document for document in documents_result.scalars().all()}
    by_product = {}
    for link in links:
        document = documents_by_id.get(str(link.contract_document_id))
        if not document:
            continue
        by_product.setdefault(str(link.deal_product_id), []).append({
            "document_id": str(document.id),
            "number_in_contract": document.number_in_contract,
            "amount": document.amount,
        })
    for item in deal_products:
        setattr(item, "invoice_links", by_product.get(str(item.id), []))
    return deal_products

# Categories
@router.get("/categories/", response_model=List[ProductCategoryResponse])
async def get_product_categories(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    try:
        return await ProductCategory.get_all(db, skip=skip, limit=limit)
    except Exception as exc:
        print(f"Error getting product categories: {exc}")
        return []

@router.post("/categories/", response_model=ProductCategoryResponse)
async def create_product_category(
    category: ProductCategoryCreate,
    db: AsyncSession = Depends(get_db)
):
    try:
        return await ProductCategory.create(db, **category.dict())
    except Exception as exc:
        print(f"Error creating product category: {exc}")
        raise HTTPException(status_code=400, detail="Failed to create category")

@router.get("/categories/{category_id}", response_model=ProductCategoryResponse)
async def get_product_category(
    category_id: str,
    db: AsyncSession = Depends(get_db)
):
    category = await ProductCategory.get_by_id(db, category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    return category

@router.put("/categories/{category_id}", response_model=ProductCategoryResponse)
async def update_product_category(
    category_id: str,
    category_update: ProductCategoryUpdate,
    db: AsyncSession = Depends(get_db)
):
    try:
        category = await ProductCategory.update(db, category_id, **category_update.dict(exclude_unset=True))
        if not category:
            raise HTTPException(status_code=404, detail="Category not found")
        return category
    except Exception as exc:
        print(f"Error updating product category {category_id}: {exc}")
        raise HTTPException(status_code=400, detail="Failed to update category")

@router.delete("/categories/{category_id}")
async def delete_product_category(
    category_id: str,
    db: AsyncSession = Depends(get_db)
):
    success = await ProductCategory.delete(db, category_id)
    if not success:
        raise HTTPException(status_code=404, detail="Category not found")
    return {"message": "Category deleted"}

# Products
@router.get("/", response_model=List[ProductResponse])
async def get_products(
    skip: int = 0,
    limit: int = 100,
    category_id: Optional[str] = None,
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    try:
        if search:
            return await Product.search(db, search, skip=skip, limit=limit)
        if category_id:
            return await Product.get_by_category(db, category_id)
        return await Product.get_all(db, skip=skip, limit=limit)
    except Exception as exc:
        print(f"Error getting products: {exc}")
        return []

@router.post("/", response_model=ProductResponse)
async def create_product(
    product: ProductCreate,
    db: AsyncSession = Depends(get_db)
):
    try:
        return await Product.create(db, **product.dict())
    except Exception as exc:
        print(f"Error creating product: {exc}")
        raise HTTPException(status_code=400, detail="Failed to create product")

@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(
    product_id: str,
    db: AsyncSession = Depends(get_db)
):
    product = await Product.get_by_id(db, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

@router.put("/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: str,
    product_update: ProductUpdate,
    db: AsyncSession = Depends(get_db)
):
    try:
        product = await Product.update(db, product_id, **product_update.dict(exclude_unset=True))
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        return product
    except Exception as exc:
        print(f"Error updating product {product_id}: {exc}")
        raise HTTPException(status_code=400, detail="Failed to update product")

@router.delete("/{product_id}")
async def delete_product(
    product_id: str,
    db: AsyncSession = Depends(get_db)
):
    success = await Product.delete(db, product_id)
    if not success:
        raise HTTPException(status_code=404, detail="Product not found")
    return {"message": "Product deleted"}

# Deal products
@router.get("/deal/{deal_id}", response_model=List[DealProductResponse])
async def get_deal_products(
    deal_id: str,
    db: AsyncSession = Depends(get_db)
):
    try:
        items = await DealProduct.get_by_deal(db, deal_id)
        await _attach_invoice_links(db, items)
        return items
    except Exception as exc:
        print(f"Error getting deal products for deal {deal_id}: {exc}")
        return []

@router.post("/deal/", response_model=DealProductResponse)
async def add_product_to_deal(
    deal_product: DealProductCreate,
    db: AsyncSession = Depends(get_db)
):
    try:
        deal = await Deal.get_by_id(db, deal_product.deal_id)
        if not deal:
            raise HTTPException(status_code=404, detail="Deal not found")

        product = await Product.get_by_id(db, deal_product.product_id)
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")

        if not deal_product.unit:
            data = deal_product.dict()
            data["unit"] = getattr(product, "unit", None) or "pcs"
            deal_product = DealProductCreate(**data)

        db_deal_product = await DealProduct.create(db, **deal_product.dict())
        await Deal.calculate_total_value(db, str(deal.id))
        return db_deal_product
    except HTTPException:
        raise
    except Exception as exc:
        print(f"Error adding product to deal: {exc}")
        raise HTTPException(status_code=400, detail="Failed to add product to deal")

@router.get("/deal/item/{deal_product_id}", response_model=DealProductResponse)
async def get_deal_product(
    deal_product_id: str,
    db: AsyncSession = Depends(get_db)
):
    deal_product = await DealProduct.get_by_id(db, deal_product_id)
    if not deal_product:
        raise HTTPException(status_code=404, detail="Deal product not found")
    return deal_product

@router.put("/deal/{deal_product_id}", response_model=DealProductResponse)
async def update_deal_product(
    deal_product_id: str,
    deal_product_update: DealProductUpdate,
    db: AsyncSession = Depends(get_db)
):
    try:
        deal_product = await DealProduct.update(db, deal_product_id, **deal_product_update.dict(exclude_unset=True))
        if not deal_product:
            raise HTTPException(status_code=404, detail="Deal product not found")
        await Deal.calculate_total_value(db, str(deal_product.deal_id))
        return deal_product
    except HTTPException:
        raise
    except Exception as exc:
        print(f"Error updating deal product {deal_product_id}: {exc}")
        raise HTTPException(status_code=400, detail="Failed to update deal product")

@router.delete("/deal/{deal_product_id}")
async def remove_product_from_deal(
    deal_product_id: str,
    db: AsyncSession = Depends(get_db)
):
    deal_product = await DealProduct.get_by_id(db, deal_product_id)
    if not deal_product:
        raise HTTPException(status_code=404, detail="Deal product not found")

    deal_id = str(deal_product.deal_id)
    success = await DealProduct.delete(db, deal_product_id)
    if not success:
        raise HTTPException(status_code=404, detail="Deal product not found")

    await Deal.calculate_total_value(db, deal_id)
    return {"message": "Deal product deleted"}

@router.post("/deal/{deal_id}/quick-add/{product_id}")
async def quick_add_product_to_deal(
    deal_id: str,
    product_id: str,
    quantity: float = 1.0,
    discount_percent: float = 0.0,
    db: AsyncSession = Depends(get_db)
):
    try:
        deal = await Deal.get_by_id(db, deal_id)
        if not deal:
            raise HTTPException(status_code=404, detail="Deal not found")

        product = await Product.get_by_id(db, product_id)
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")

        data = {
            "deal_id": str(deal.id),
            "product_id": str(product.id),
            "quantity": quantity,
            "unit": getattr(product, "unit", None) or "pcs",
            "unit_price": product.base_price,
            "discount_percent": discount_percent,
            "tax_rate": 0.0,
            "currency": "RUB",
            "status": "planned",
        }

        db_deal_product = await DealProduct.create(db, **data)
        return {
            "message": "Product added to deal",
            "deal_product": {
                "id": str(db_deal_product.id),
                "product_name": product.name,
                "quantity": quantity,
                "final_price": db_deal_product.final_price,
            },
        }
    except HTTPException:
        raise
    except Exception as exc:
        print(f"Error quick adding product to deal: {exc}")
        raise HTTPException(status_code=400, detail="Failed to add product to deal")

# Lead products
@router.get("/lead/{lead_id}", response_model=List[LeadProductResponse])
async def get_lead_products(
    lead_id: str,
    db: AsyncSession = Depends(get_db)
):
    try:
        return await LeadProduct.get_by_lead(db, lead_id)
    except Exception as exc:
        print(f"Error getting lead products for lead {lead_id}: {exc}")
        return []


@router.post("/lead/", response_model=LeadProductResponse)
async def add_product_to_lead(
    lead_product: LeadProductCreate,
    db: AsyncSession = Depends(get_db)
):
    try:
        lead = await Lead.get_by_id(db, lead_product.lead_id)
        if not lead:
            raise HTTPException(status_code=404, detail="Lead not found")

        product = await Product.get_by_id(db, lead_product.product_id)
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")

        if not lead_product.unit:
            data = lead_product.dict()
            data["unit"] = getattr(product, "unit", None) or "pcs"
            lead_product = LeadProductCreate(**data)

        db_lead_product = await LeadProduct.create(db, **lead_product.dict())
        await Lead.calculate_total_value(db, str(lead.id))
        return db_lead_product
    except HTTPException:
        raise
    except Exception as exc:
        print(f"Error adding product to lead: {exc}")
        raise HTTPException(status_code=400, detail="Failed to add product to lead")


@router.get("/lead/item/{lead_product_id}", response_model=LeadProductResponse)
async def get_lead_product(
    lead_product_id: str,
    db: AsyncSession = Depends(get_db)
):
    lead_product = await LeadProduct.get_by_id(db, lead_product_id)
    if not lead_product:
        raise HTTPException(status_code=404, detail="Lead product not found")
    return lead_product


@router.put("/lead/{lead_product_id}", response_model=LeadProductResponse)
async def update_lead_product(
    lead_product_id: str,
    lead_product_update: LeadProductUpdate,
    db: AsyncSession = Depends(get_db)
):
    try:
        lead_product = await LeadProduct.update(db, lead_product_id, **lead_product_update.dict(exclude_unset=True))
        if not lead_product:
            raise HTTPException(status_code=404, detail="Lead product not found")
        await Lead.calculate_total_value(db, str(lead_product.lead_id))
        return lead_product
    except HTTPException:
        raise
    except Exception as exc:
        print(f"Error updating lead product {lead_product_id}: {exc}")
        raise HTTPException(status_code=400, detail="Failed to update lead product")


@router.delete("/lead/{lead_product_id}")
async def remove_product_from_lead(
    lead_product_id: str,
    db: AsyncSession = Depends(get_db)
):
    lead_product = await LeadProduct.get_by_id(db, lead_product_id)
    if not lead_product:
        raise HTTPException(status_code=404, detail="Lead product not found")

    lead_id = str(lead_product.lead_id)
    success = await LeadProduct.delete(db, lead_product_id)
    if not success:
        raise HTTPException(status_code=404, detail="Lead product not found")

    await Lead.calculate_total_value(db, lead_id)
    return {"message": "Lead product deleted"}
