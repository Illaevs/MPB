"""
Task Auctions Router - API для аукционов на задачи
"""
import uuid
from datetime import datetime, date, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from pydantic import BaseModel

from app.database.session import get_db
from app.models import TaskAuction, TaskAuctionBid, Task, User, Company, IncomeExpenseEntry


router = APIRouter(prefix="/task-auctions", tags=["Task Auctions"])


# Schemas
class TaskAuctionItem(BaseModel):
    title: str
    description: Optional[str] = None
    budget: float
    allow_custom_price: bool = False


class TaskAuctionCreate(BaseModel):
    title: str
    description: Optional[str] = None
    budget: Optional[float] = None
    deal_id: Optional[str] = None
    category_code: Optional[str] = None
    allow_custom_price: bool = False
    is_block: bool = False
    items: Optional[List[TaskAuctionItem]] = None


class TaskAuctionUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    budget: Optional[float] = None
    deal_id: Optional[str] = None
    category_code: Optional[str] = None
    allow_custom_price: Optional[bool] = None


class TaskAuctionBidCreate(BaseModel):
    bid_price: float
    comment: Optional[str] = None
    covers_children: bool = False


class TaskAuctionBidUpdate(BaseModel):
    bid_price: Optional[float] = None
    comment: Optional[str] = None


class SelectWinnerRequest(BaseModel):
    bid_id: str
    category_code: Optional[str] = None
    payer_id: Optional[str] = None
    payee_id: Optional[str] = None
    due_date: Optional[date] = None


class RateExecutorRequest(BaseModel):
    rating: int  # 1-5


# Helper functions
def _to_date(value) -> Optional[date]:
    if value is None:
        return None
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, str):
        try:
            return date.fromisoformat(value)
        except ValueError:
            return None
    return None

def _plan_date_from_due(due_date_value) -> Optional[date]:
    due_date = _to_date(due_date_value)
    if not due_date:
        return None
    return due_date + timedelta(days=14)


async def _get_children(db: AsyncSession, block_id: str) -> List[TaskAuction]:
    result = await db.execute(
        select(TaskAuction).where(TaskAuction.block_id == block_id).order_by(TaskAuction.created_at.asc())
    )
    return result.scalars().all()


async def _count_bids(db: AsyncSession, auction_id: str) -> int:
    result = await db.execute(select(TaskAuctionBid).where(TaskAuctionBid.auction_id == auction_id))
    return len(result.scalars().all())

def _build_auction_response(
    auction: TaskAuction,
    bids_count: int = 0,
    children: Optional[List[dict]] = None,
) -> dict:
    payload = {
        "id": auction.id,
        "title": auction.title,
        "description": auction.description,
        "budget": auction.budget,
        "deal_id": auction.deal_id,
        "category_code": auction.category_code,
        "allow_custom_price": auction.allow_custom_price,
        "is_block": auction.is_block,
        "block_id": auction.block_id,
        "status": auction.status,
        "winner_id": auction.winner_id,
        "winner_bid_id": auction.winner_bid_id,
        "created_task_id": auction.created_task_id,
        "created_by_id": auction.created_by_id,
        "created_at": auction.created_at.isoformat() if auction.created_at else None,
        "bids_count": bids_count,
    }
    if children is not None:
        payload["children"] = children
    return payload


def _build_bid_response(bid: TaskAuctionBid) -> dict:
    user = bid.user
    return {
        "id": bid.id,
        "auction_id": bid.auction_id,
        "user_id": bid.user_id,
        "bid_price": bid.bid_price,
        "comment": bid.comment,
        "covers_children": bid.covers_children,
        "created_at": bid.created_at.isoformat() if bid.created_at else None,
        "user": {
            "id": user.id,
            "full_name": user.full_name,
            "email": user.email,
            "rating": user.rating or 0.0,
            "rating_count": user.rating_count or 0,
        } if user else None
    }


# ========== AUCTION CRUD ==========

@router.get("/")
async def list_auctions(
    status: Optional[str] = None,
    deal_id: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db)
):
    """List all auctions with optional filters."""
    auctions = await TaskAuction.get_all(
        db,
        skip=skip,
        limit=limit,
        status=status,
        deal_id=deal_id,
        parent_only=True,
        include_children=True,
    )

    result = []
    for auction in auctions:
        bids_count = await _count_bids(db, auction.id)
        children_payload = None
        if auction.is_block:
            children_payload = []
            children = sorted(auction.children or [], key=lambda child: child.created_at or datetime.min)
            for child in children:
                child_bids_count = await _count_bids(db, child.id)
                children_payload.append(_build_auction_response(child, child_bids_count))
        payload = _build_auction_response(auction, bids_count, children_payload)
        if auction.is_block and children_payload is not None:
            payload["budget"] = sum(child.get("budget", 0) or 0 for child in children_payload)
        result.append(payload)

    return {"items": result}


@router.post("/")
async def create_auction(
    data: TaskAuctionCreate,
    created_by_id: Optional[str] = None,  # TODO: get from auth
    db: AsyncSession = Depends(get_db)
):
    """Create a new task auction."""
    if data.is_block:
        if not data.items:
            raise HTTPException(status_code=400, detail="items required for auction block")
        items = [item for item in data.items if item.title and item.budget is not None]
        if not items:
            raise HTTPException(status_code=400, detail="Block must have at least one item")
        total_budget = sum(float(item.budget) for item in items)
        block = await TaskAuction.create(
            db,
            id=str(uuid.uuid4()),
            title=data.title,
            description=data.description,
            budget=total_budget,
            deal_id=data.deal_id,
            category_code=data.category_code,
            allow_custom_price=False,
            status="new",
            created_by_id=created_by_id,
            is_block=True,
            block_id=None,
        )
        children_payload = []
        for item in items:
            child = await TaskAuction.create(
                db,
                id=str(uuid.uuid4()),
                title=item.title,
                description=item.description,
                budget=item.budget,
                deal_id=data.deal_id,
                category_code=data.category_code,
                allow_custom_price=item.allow_custom_price,
                status="new",
                created_by_id=created_by_id,
                is_block=False,
                block_id=block.id,
            )
            children_payload.append(_build_auction_response(child, 0))
        payload = _build_auction_response(block, 0, children_payload)
        payload["budget"] = total_budget
        return payload

    if data.budget is None:
        raise HTTPException(status_code=400, detail="budget is required")
    auction = await TaskAuction.create(
        db,
        id=str(uuid.uuid4()),
        title=data.title,
        description=data.description,
        budget=data.budget,
        deal_id=data.deal_id,
        category_code=data.category_code,
        allow_custom_price=data.allow_custom_price,
        status="new",
        created_by_id=created_by_id,
        is_block=False,
        block_id=None,
    )
    return _build_auction_response(auction)


@router.get("/{auction_id}")
async def get_auction(
    auction_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get auction details with all bids."""
    auction = await TaskAuction.get_by_id(db, auction_id)
    if not auction:
        raise HTTPException(status_code=404, detail="Auction not found")
    
    bids = await TaskAuctionBid.get_by_auction(db, auction_id)

    children_payload = None
    if auction.is_block:
        children_payload = []
        for child in await _get_children(db, auction.id):
            child_bids_count = await _count_bids(db, child.id)
            children_payload.append(_build_auction_response(child, child_bids_count))

    return {
        **_build_auction_response(auction, len(bids), children_payload),
        "bids": [_build_bid_response(bid) for bid in bids]
    }


@router.patch("/{auction_id}")
async def update_auction(
    auction_id: str,
    data: TaskAuctionUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update auction (only if status is 'new')."""
    auction = await TaskAuction.get_by_id(db, auction_id)
    if not auction:
        raise HTTPException(status_code=404, detail="Auction not found")
    
    if auction.status != "new":
        raise HTTPException(status_code=400, detail="Cannot edit non-new auction")
    
    update_data = data.model_dump(exclude_unset=True)
    if update_data:
        auction = await TaskAuction.update(db, auction_id, **update_data)
    
    bids = await TaskAuctionBid.get_by_auction(db, auction_id)
    return _build_auction_response(auction, len(bids))


@router.delete("/{auction_id}")
async def cancel_auction(
    auction_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Cancel an auction (set status to cancelled)."""
    auction = await TaskAuction.get_by_id(db, auction_id)
    if not auction:
        raise HTTPException(status_code=404, detail="Auction not found")
    
    if auction.status == "awarded":
        raise HTTPException(status_code=400, detail="Cannot cancel awarded auction")

    if auction.is_block:
        children = await _get_children(db, auction.id)
        if any(child.status == "awarded" for child in children):
            raise HTTPException(status_code=400, detail="Cannot cancel block with awarded tasks")
        for child in children:
            await TaskAuction.update(db, child.id, status="cancelled")

    await TaskAuction.update(db, auction_id, status="cancelled")
    return {"message": "Auction cancelled"}


@router.delete("/{auction_id}/hard")
async def delete_auction(
    auction_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Hard delete an auction (admin use)."""
    auction = await TaskAuction.get_by_id(db, auction_id)
    if not auction:
        raise HTTPException(status_code=404, detail="Auction not found")

    if auction.status == "awarded" and auction.created_task_id:
        task = await Task.get_by_id(db, auction.created_task_id)
        if task:
            raise HTTPException(status_code=400, detail="Delete the created task before deleting this auction")

    if auction.is_block:
        from sqlalchemy import delete
        children = await _get_children(db, auction.id)
        for child in children:
            if child.created_task_id:
                task = await Task.get_by_id(db, child.created_task_id)
                if task:
                    raise HTTPException(status_code=400, detail="Delete tasks created from block before deleting it")
        await db.execute(delete(TaskAuction).where(TaskAuction.block_id == auction.id))

    await db.delete(auction)
    await db.commit()
    return {"message": "Auction deleted"}


@router.post("/{auction_id}/select-winner")
async def select_winner(
    auction_id: str,
    data: SelectWinnerRequest,
    db: AsyncSession = Depends(get_db)
):
    """Select winner from bids and create a task."""
    auction = await TaskAuction.get_by_id(db, auction_id)
    if not auction:
        raise HTTPException(status_code=404, detail="Auction not found")
    
    if auction.status != "new":
        raise HTTPException(status_code=400, detail="Auction is not open")
    
    bid = await TaskAuctionBid.get_by_id(db, data.bid_id)
    if not bid or bid.auction_id != auction_id:
        raise HTTPException(status_code=404, detail="Bid not found")

    if auction.is_block:
        children = await _get_children(db, auction.id)
        if not children:
            raise HTTPException(status_code=400, detail="Block has no items")

        requires_budget = any((child.budget or 0) > 0 for child in children)
        category_code = data.category_code or auction.category_code
        if requires_budget:
            if not category_code or not data.payer_id or not data.payee_id or not data.due_date:
                raise HTTPException(status_code=400, detail="category_code, payer_id, payee_id and due_date required for task with budget")
            payer = await Company.get_by_id(db, data.payer_id)
            if not payer:
                raise HTTPException(status_code=404, detail="Payer company not found")
            payee = await Company.get_by_id(db, data.payee_id)
            if not payee:
                raise HTTPException(status_code=404, detail="Payee company not found")

        task_ids = []
        for child in children:
            child_budget = child.budget or 0
            task = await Task.create(
                db,
                id=str(uuid.uuid4()),
                title=child.title,
                description=child.description,
                deal_id=child.deal_id or auction.deal_id or "00000000-0000-0000-0000-000000000000",
                budget=child_budget,
                category_code=category_code if child_budget > 0 else None,
                payer_id=data.payer_id if child_budget > 0 else None,
                payee_id=data.payee_id if child_budget > 0 else None,
                due_date=data.due_date if child_budget > 0 else None,
                source_auction_id=child.id,
                assigned_to_user_id=bid.user_id,
                status="new",
                priority="normal",
            )

            if child_budget > 0:
                plan_date = _plan_date_from_due(data.due_date)
                if not plan_date:
                    raise HTTPException(status_code=400, detail="Invalid due_date")
                entry = IncomeExpenseEntry(
                    direction="expense",
                    amount=abs(child_budget),
                    plan_date=plan_date,
                    payer_id=data.payer_id,
                    payee_id=data.payee_id,
                    deal_id=child.deal_id or auction.deal_id,
                    category_code=category_code
                )
                db.add(entry)
                await db.commit()
                await db.refresh(entry)
                task = await Task.update(db, task.id, income_expense_id=str(entry.id))

            child_bid = await TaskAuctionBid.get_by_user_and_auction(db, bid.user_id, child.id)
            await TaskAuction.update(
                db,
                child.id,
                status="awarded",
                winner_id=bid.user_id,
                winner_bid_id=child_bid.id if child_bid else None,
                created_task_id=task.id,
            )
            task_ids.append(task.id)

        await TaskAuction.update(
            db,
            auction_id,
            status="awarded",
            winner_id=bid.user_id,
            winner_bid_id=bid.id,
            created_task_id=None,
        )

        return {
            "message": "Winner selected",
            "task_ids": task_ids,
            "winner_user_id": bid.user_id
        }

    budget_value = bid.bid_price
    category_code = data.category_code or auction.category_code
    if budget_value and budget_value > 0:
        if not category_code or not data.payer_id or not data.payee_id or not data.due_date:
            raise HTTPException(status_code=400, detail="category_code, payer_id, payee_id and due_date required for task with budget")
        payer = await Company.get_by_id(db, data.payer_id)
        if not payer:
            raise HTTPException(status_code=404, detail="Payer company not found")
        payee = await Company.get_by_id(db, data.payee_id)
        if not payee:
            raise HTTPException(status_code=404, detail="Payee company not found")

    # Create task from auction
    task = await Task.create(
        db,
        id=str(uuid.uuid4()),
        title=auction.title,
        description=auction.description,
        deal_id=auction.deal_id or "00000000-0000-0000-0000-000000000000",  # fallback
        budget=budget_value,
        category_code=category_code,
        payer_id=data.payer_id,
        payee_id=data.payee_id,
        due_date=data.due_date,
        source_auction_id=auction.id,
        assigned_to_user_id=bid.user_id,
        status="new",
        priority="normal",
    )

    if budget_value and budget_value > 0:
        plan_date = _plan_date_from_due(data.due_date)
        if not plan_date:
            raise HTTPException(status_code=400, detail="Invalid due_date")
        entry = IncomeExpenseEntry(
            direction="expense",
            amount=abs(budget_value),
            plan_date=plan_date,
            payer_id=data.payer_id,
            payee_id=data.payee_id,
            deal_id=auction.deal_id,
            category_code=category_code
        )
        db.add(entry)
        await db.commit()
        await db.refresh(entry)
        task = await Task.update(db, task.id, income_expense_id=str(entry.id))

    # Update auction
    await TaskAuction.update(
        db,
        auction_id,
        status="awarded",
        winner_id=bid.user_id,
        winner_bid_id=bid.id,
        created_task_id=task.id
    )

    if auction.block_id:
        siblings = await _get_children(db, auction.block_id)
        if siblings and all(child.status == "awarded" for child in siblings):
            await TaskAuction.update(db, auction.block_id, status="awarded")

    return {
        "message": "Winner selected",
        "task_id": task.id,
        "winner_user_id": bid.user_id
    }


# ========== BIDS CRUD ==========

@router.get("/{auction_id}/bids")
async def list_bids(
    auction_id: str,
    db: AsyncSession = Depends(get_db)
):
    """List all bids for an auction."""
    auction = await TaskAuction.get_by_id(db, auction_id)
    if not auction:
        raise HTTPException(status_code=404, detail="Auction not found")
    
    bids = await TaskAuctionBid.get_by_auction(db, auction_id)
    return {"items": [_build_bid_response(bid) for bid in bids]}


@router.post("/{auction_id}/bids")
async def create_bid(
    auction_id: str,
    data: TaskAuctionBidCreate,
    user_id: Optional[str] = None,  # Accept as query param
    db: AsyncSession = Depends(get_db)
):
    """Submit a bid for an auction."""
    if not user_id:
        raise HTTPException(status_code=400, detail="user_id is required")
    auction = await TaskAuction.get_by_id(db, auction_id)
    if not auction:
        raise HTTPException(status_code=404, detail="Auction not found")
    
    if auction.status != "new":
        raise HTTPException(status_code=400, detail="Auction is not open")
    
    # Check if user already has a bid
    existing = await TaskAuctionBid.get_by_user_and_auction(db, user_id, auction_id)
    if existing:
        raise HTTPException(status_code=400, detail="You already have a bid. Use PATCH to update.")
    
    # If fixed price, set bid_price to budget
    bid_price = data.bid_price if auction.allow_custom_price else auction.budget
    covers_children = bool(data.covers_children) if auction.is_block else False

    if auction.is_block and covers_children:
        children = await _get_children(db, auction.id)
        for child in children:
            existing_child = await TaskAuctionBid.get_by_user_and_auction(db, user_id, child.id)
            if existing_child:
                continue
            child_bid_price = child.budget
            await TaskAuctionBid.create(
                db,
                id=str(uuid.uuid4()),
                auction_id=child.id,
                user_id=user_id,
                bid_price=child_bid_price,
                comment=data.comment,
                covers_children=False,
            )

    bid = await TaskAuctionBid.create(
        db,
        id=str(uuid.uuid4()),
        auction_id=auction_id,
        user_id=user_id,
        bid_price=bid_price,
        comment=data.comment,
        covers_children=covers_children,
    )
    
    # Reload with user relationship
    bids = await TaskAuctionBid.get_by_auction(db, auction_id)
    bid = next((b for b in bids if b.id == bid.id), bid)
    
    return _build_bid_response(bid)


@router.patch("/{auction_id}/bids/{bid_id}")
async def update_bid(
    auction_id: str,
    bid_id: str,
    data: TaskAuctionBidUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update a bid."""
    auction = await TaskAuction.get_by_id(db, auction_id)
    if not auction:
        raise HTTPException(status_code=404, detail="Auction not found")
    
    if auction.status != "new":
        raise HTTPException(status_code=400, detail="Auction is not open")
    
    bid = await TaskAuctionBid.get_by_id(db, bid_id)
    if not bid or bid.auction_id != auction_id:
        raise HTTPException(status_code=404, detail="Bid not found")
    
    update_data = data.model_dump(exclude_unset=True)
    
    # If fixed price, ignore bid_price update
    if not auction.allow_custom_price and "bid_price" in update_data:
        del update_data["bid_price"]
    
    if update_data:
        bid = await TaskAuctionBid.update(db, bid_id, **update_data)
    
    # Reload with user relationship
    bids = await TaskAuctionBid.get_by_auction(db, auction_id)
    bid = next((b for b in bids if b.id == bid_id), bid)
    
    return _build_bid_response(bid)


@router.delete("/{auction_id}/bids/{bid_id}")
async def delete_bid(
    auction_id: str,
    bid_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Withdraw a bid."""
    auction = await TaskAuction.get_by_id(db, auction_id)
    if not auction:
        raise HTTPException(status_code=404, detail="Auction not found")
    
    if auction.status != "new":
        raise HTTPException(status_code=400, detail="Auction is not open")
    
    bid = await TaskAuctionBid.get_by_id(db, bid_id)
    if not bid or bid.auction_id != auction_id:
        raise HTTPException(status_code=404, detail="Bid not found")
    
    await TaskAuctionBid.delete(db, bid_id)
    return {"message": "Bid withdrawn"}


# ========== TASK RATING ==========

@router.post("/tasks/{task_id}/rate")
async def rate_executor(
    task_id: str,
    data: RateExecutorRequest,
    db: AsyncSession = Depends(get_db)
):
    """Rate the executor of a completed task (1-5 stars)."""
    if data.rating < 1 or data.rating > 5:
        raise HTTPException(status_code=400, detail="Rating must be 1-5")
    
    task = await Task.get_by_id(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    if task.status != "completed":
        raise HTTPException(status_code=400, detail="Task must be completed to rate")
    
    if task.executor_rating:
        raise HTTPException(status_code=400, detail="Task already rated")
    
    if not task.assigned_to_user_id:
        raise HTTPException(status_code=400, detail="Task has no assigned user")
    
    # Update task rating
    await Task.update(db, task_id, executor_rating=data.rating)

    # Recalculate penalty/bonus if budget exists
    if task.budget and task.budget > 0:
        from app.routers.tasks import calculate_penalty_coefficients
        rating_coef, deadline_coef, final_budget, penalty_amount = await calculate_penalty_coefficients(
            db,
            task,
            executor_rating=data.rating
        )
        if rating_coef is not None:
            await Task.update(
                db,
                task_id,
                rating_coefficient=rating_coef,
                deadline_coefficient=deadline_coef,
                final_budget=final_budget,
                penalty_amount=penalty_amount
            )
    
    # Update user's average rating
    user = await User.get_by_id(db, task.assigned_to_user_id)
    if user:
        current_rating = user.rating or 0.0
        current_count = user.rating_count or 0
        
        new_count = current_count + 1
        new_rating = ((current_rating * current_count) + data.rating) / new_count
        
        await User.update(db, user.id, rating=round(new_rating, 2), rating_count=new_count)
    
    return {"message": "Rating saved", "new_user_rating": round(new_rating, 2) if user else None}
