"""
Subcontractor cards API Router (same logic as deals)
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Body, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.models import SubcontractorCard
from app.schemas.subcontractor import SubcontractorCreate, SubcontractorResponse

router = APIRouter()


@router.get("/", response_model=List[SubcontractorResponse])
async def get_subcontractors(
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    min_contract_value: Optional[float] = None,
    max_contract_value: Optional[float] = None,
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    try:
        cards = await SubcontractorCard.get_filtered(
            db,
            skip=skip,
            limit=limit,
            status=status,
            min_contract_value=min_contract_value,
            max_contract_value=max_contract_value,
            search=search
        )
        for card in cards:
            if hasattr(card, 'id') and card.id:
                card.id = str(card.id)
        return cards
    except Exception as e:
        print(f"Error getting subcontractor cards: {e}")
        return []


@router.post("/", response_model=SubcontractorResponse)
async def create_subcontractor(
    card: SubcontractorCreate,
    db: AsyncSession = Depends(get_db)
):
    try:
        db_card = await SubcontractorCard.create(db, **card.dict())
        if hasattr(db_card, 'id') and db_card.id:
            db_card.id = str(db_card.id)
        return db_card
    except Exception as exc:
        await db.rollback()
        print(f"Error creating subcontractor card: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/{card_id}", response_model=SubcontractorResponse)
async def get_subcontractor(
    card_id: str,
    db: AsyncSession = Depends(get_db)
):
    card = await SubcontractorCard.get_by_id(db, card_id)
    if not card:
        raise HTTPException(status_code=404, detail="Карточка субподрядчика не найдена")
    return card


@router.put("/{card_id}")
async def update_subcontractor(
    card_id: str,
    card_update: dict = Body(None),
    db: AsyncSession = Depends(get_db)
):
    filtered_data = {k: v for k, v in card_update.items() if v is not None}
    if not filtered_data:
        raise HTTPException(status_code=400, detail="??? ?????? ??? ??????????")
    try:
        card = await SubcontractorCard.update(db, card_id, **filtered_data)
        if not card:
            raise HTTPException(status_code=404, detail="???????? ????????????? ?? ???????")
        return card
    except HTTPException:
        raise
    except Exception as exc:
        await db.rollback()
        print(f"Error updating subcontractor card: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


@router.patch("/{card_id}/vat")
async def update_subcontractor_vat(
    card_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    try:
        vat_data = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Ошибка чтения данных")

    update_data = {}
    if 'vat_rate' in vat_data:
        update_data['vat_rate'] = vat_data['vat_rate']
    if 'vat_included' in vat_data:
        update_data['vat_included'] = vat_data['vat_included']

    if not update_data:
        raise HTTPException(status_code=400, detail="Нет данных для обновления НДС")

    card = await SubcontractorCard.update(db, card_id, **update_data)
    if not card:
        raise HTTPException(status_code=404, detail="Субподрядчик не найден")
    return {"message": "Настройки НДС обновлены"}


@router.delete("/{card_id}")
async def delete_subcontractor(
    card_id: str,
    db: AsyncSession = Depends(get_db)
):
    success = await SubcontractorCard.delete(db, card_id)
    if not success:
        raise HTTPException(status_code=404, detail="Карточка субподрядчика не найдена")
    return {"message": "Карточка субподрядчика удалена"}
