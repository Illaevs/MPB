"""
Penalty Rules API Router
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.models import PenaltyRule
from app.schemas.penalty_rule import PenaltyRuleCreate, PenaltyRuleUpdate, PenaltyRuleResponse

router = APIRouter()


@router.get("/", response_model=List[PenaltyRuleResponse])
async def get_penalty_rules(
    only_active: bool = False,
    rule_type: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """Получить все правила штрафов"""
    if rule_type:
        rules = await PenaltyRule.get_by_type(db, rule_type, only_active=only_active)
    else:
        rules = await PenaltyRule.get_all(db, only_active=only_active)
    return rules


@router.get("/{rule_id}", response_model=PenaltyRuleResponse)
async def get_penalty_rule(
    rule_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Получить правило по ID"""
    rule = await PenaltyRule.get_by_id(db, rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail="Правило не найдено")
    return rule


@router.post("/", response_model=PenaltyRuleResponse)
async def create_penalty_rule(
    rule_data: PenaltyRuleCreate,
    db: AsyncSession = Depends(get_db)
):
    """Создать новое правило"""
    rule = await PenaltyRule.create(db, **rule_data.dict())
    return rule


@router.patch("/{rule_id}", response_model=PenaltyRuleResponse)
async def update_penalty_rule(
    rule_id: str,
    rule_data: PenaltyRuleUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Обновить правило"""
    rule = await PenaltyRule.get_by_id(db, rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail="Правило не найдено")
    
    update_data = {k: v for k, v in rule_data.dict().items() if v is not None}
    if not update_data:
        return rule
    
    updated_rule = await PenaltyRule.update(db, rule_id, **update_data)
    return updated_rule


@router.delete("/{rule_id}")
async def delete_penalty_rule(
    rule_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Удалить правило"""
    success = await PenaltyRule.delete(db, rule_id)
    if not success:
        raise HTTPException(status_code=404, detail="Правило не найдено")
    return {"message": "Правило удалено"}


@router.post("/seed-defaults")
async def seed_default_rules(
    db: AsyncSession = Depends(get_db)
):
    """Создать правила по умолчанию"""
    # Проверяем есть ли уже правила
    existing = await PenaltyRule.get_all(db)
    if existing:
        return {"message": f"Правила уже существуют ({len(existing)} шт.)"}
    
    # Правила для оценок
    rating_rules = [
        {"rule_type": "rating", "condition_min": 5, "condition_max": 5, "coefficient": 1.1, "description": "5 звёзд - бонус 10%", "sort_order": 1},
        {"rule_type": "rating", "condition_min": 4, "condition_max": 4, "coefficient": 1.0, "description": "4 звезды - без изменений", "sort_order": 2},
        {"rule_type": "rating", "condition_min": 3, "condition_max": 3, "coefficient": 0.9, "description": "3 звезды - штраф 10%", "sort_order": 3},
        {"rule_type": "rating", "condition_min": 2, "condition_max": 2, "coefficient": 0.7, "description": "2 звезды - штраф 30%", "sort_order": 4},
        {"rule_type": "rating", "condition_min": 1, "condition_max": 1, "coefficient": 0.5, "description": "1 звезда - штраф 50%", "sort_order": 5},
    ]
    
    # Правила для сроков (в процентах отклонения)
    deadline_rules = [
        {"rule_type": "deadline", "condition_min": -100, "condition_max": -15, "coefficient": 1.1, "description": "Быстрее на 15%+ - бонус 10%", "sort_order": 1},
        {"rule_type": "deadline", "condition_min": -15, "condition_max": 10, "coefficient": 1.0, "description": "В срок (±10%) - без изменений", "sort_order": 2},
        {"rule_type": "deadline", "condition_min": 10, "condition_max": 25, "coefficient": 0.9, "description": "Опоздание 10-25% - штраф 10%", "sort_order": 3},
        {"rule_type": "deadline", "condition_min": 25, "condition_max": 50, "coefficient": 0.75, "description": "Опоздание 25-50% - штраф 25%", "sort_order": 4},
        {"rule_type": "deadline", "condition_min": 50, "condition_max": 1000, "coefficient": 0.5, "description": "Опоздание 50%+ - штраф 50%", "sort_order": 5},
    ]
    
    created = 0
    for rule_data in rating_rules + deadline_rules:
        await PenaltyRule.create(db, **rule_data)
        created += 1
    
    return {"message": f"Создано {created} правил по умолчанию"}
