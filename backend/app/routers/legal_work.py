"""
Legal work (cases) API.
"""
from typing import List

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
import httpx
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database.session import get_db
from app.models import LegalCase, LegalCaseEvent, LegalCaseEventFile, LegalCaseTask, Company, Task, Deal
from app.core.config import settings
from app.services.storage import (
    clean_name,
    ensure_path,
    upload_bytes_with_safe_extension,
    get_download_href,
    storage_available,
    delete_path,
)
from app.schemas.legal_work import (
    LegalCaseCreate,
    LegalCaseUpdate,
    LegalCaseResponse,
    LegalCaseEventCreate,
    LegalCaseEventUpdate,
    LegalCaseEventFileResponse,
    LegalCaseEventResponse,
    LegalCaseTaskLinkCreate,
    LegalCaseTaskResponse,
)


router = APIRouter()

LEGAL_WORK_ROOT_FOLDER = "Юридическая хронология"


def _legal_case_folder_name(case: LegalCase) -> str:
    parts = []
    if case.case_number:
        parts.append(case.case_number)
    if case.id:
        parts.append(str(case.id))
    label = " - ".join([p for p in parts if p]) or str(case.id)
    return clean_name(label)


def _legal_event_storage_path(case: LegalCase, event: LegalCaseEvent) -> str:
    base_root = (settings.STORAGE_LOCAL_ROOT or "").rstrip("/")
    case_folder = _legal_case_folder_name(case)
    return f"{base_root}/{LEGAL_WORK_ROOT_FOLDER}/{case_folder}/events/{event.id}"

EVENT_TYPES = {
    "\u0418\u0441\u043a\u043e\u0432\u043e\u0435 \u0437\u0430\u044f\u0432\u043b\u0435\u043d\u0438\u0435",
    "\u0425\u043e\u0434\u0430\u0442\u0430\u0439\u0441\u0442\u0432\u043e",
    "\u041f\u0438\u0441\u044c\u043c\u0435\u043d\u043d\u044b\u0435 \u043e\u0431\u044a\u044f\u0441\u043d\u0435\u043d\u0438\u044f",
    "\u041e\u0442\u0437\u044b\u0432",
    "\u0417\u0430\u0441\u0435\u0434\u0430\u043d\u0438\u0435",
      "\u0420\u0435\u0437\u043e\u043b\u044e\u0442\u0438\u0432\u043d\u0430\u044f \u0447\u0430\u0441\u0442\u044c \u0440\u0435\u0448\u0435\u043d\u0438\u044f",
      "\u041c\u043e\u0442\u0438\u0432\u0438\u0440\u043e\u0432\u0430\u043d\u043d\u043e\u0435 \u0440\u0435\u0448\u0435\u043d\u0438\u0435",
      "\u0410\u043f\u0435\u043b\u043b\u044f\u0446\u0438\u043e\u043d\u043d\u0430\u044f \u0436\u0430\u043b\u043e\u0431\u0430",
      "\u041a\u0430\u0441\u0441\u0430\u0446\u0438\u043e\u043d\u043d\u0430\u044f \u0436\u0430\u043b\u043e\u0431\u0430",
      "\u0421\u043e\u0431\u044b\u0442\u0438\u0435",
      "\u041e\u043f\u0440\u0435\u0434\u0435\u043b\u0435\u043d\u0438\u0435",
  }


async def _ensure_company(db: AsyncSession, company_id: str, field_name: str):
    if not company_id:
        return None
    company = await Company.get_by_id(db, company_id)
    if not company:
        raise HTTPException(status_code=404, detail=f"{field_name} not found")
    return company


@router.get("/", response_model=List[LegalCaseResponse])
async def list_legal_cases(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(LegalCase).options(
            selectinload(LegalCase.plaintiff),
            selectinload(LegalCase.defendant)
        )
    )
    cases = result.scalars().all()
    if not cases:
        return []

    case_ids = [case.id for case in cases]

    events_result = await db.execute(
        select(LegalCaseEvent)
        .where(LegalCaseEvent.legal_case_id.in_(case_ids))
        .order_by(LegalCaseEvent.event_date.desc(), LegalCaseEvent.created_at.desc())
    )
    events = events_result.scalars().all()
    events_map = {}
    for event in events:
        events_map.setdefault(event.legal_case_id, []).append(event)

    event_ids = [event.id for event in events]
    files_map = {}
    if event_ids:
        files_result = await db.execute(
            select(LegalCaseEventFile).where(LegalCaseEventFile.event_id.in_(event_ids))
        )
        for file_item in files_result.scalars().all():
            files_map.setdefault(file_item.event_id, []).append(file_item)

    tasks_result = await db.execute(
        select(LegalCaseTask, Task, Deal)
        .join(Task, Task.id == LegalCaseTask.task_id)
        .outerjoin(Deal, Deal.id == Task.deal_id)
        .where(LegalCaseTask.legal_case_id.in_(case_ids))
    )
    tasks_map = {}
    for link, task, deal in tasks_result.all():
        tasks_map.setdefault(link.legal_case_id, []).append((task, deal))

    response = []
    for case in cases:
        response.append({
            "id": str(case.id),
            "case_number": case.case_number,
            "judge": case.judge,
            "jurisdiction": case.jurisdiction,
            "judge_assistant": case.judge_assistant,
            "judge_assistant_phone": case.judge_assistant_phone,
            "plaintiff_id": case.plaintiff_id,
            "defendant_id": case.defendant_id,
            "plaintiff_name": case.plaintiff.name if case.plaintiff else None,
            "defendant_name": case.defendant.name if case.defendant else None,
            "description": case.description,
            "events": [
                LegalCaseEventResponse(
                    id=str(event.id),
                    legal_case_id=str(event.legal_case_id),
                    event_type=event.event_type,
                    event_date=event.event_date,
                    event_time=event.event_time,
                    courtroom=event.courtroom,
                    files=[
                        LegalCaseEventFileResponse(
                            id=str(file_item.id),
                            event_id=str(file_item.event_id),
                            file_name=file_item.file_name,
                            storage_path=file_item.storage_path or file_item.yandex_path,
                            created_at=file_item.created_at,
                        )
                        for file_item in files_map.get(event.id, [])
                    ],
                    created_at=event.created_at,
                )
                for event in events_map.get(case.id, [])
            ],
            "tasks": [
                LegalCaseTaskResponse(
                    id=str(task.id),
                    title=task.title,
                    status=task.status,
                    due_date=task.due_date,
                    deal_id=str(task.deal_id) if task.deal_id else None,
                    deal_title=deal.title if deal else None,
                )
                for task, deal in tasks_map.get(case.id, [])
            ],
            "created_at": case.created_at,
            "updated_at": case.updated_at,
        })
    return response


@router.get("/{case_id}", response_model=LegalCaseResponse)
async def get_legal_case(case_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(LegalCase)
        .options(selectinload(LegalCase.plaintiff), selectinload(LegalCase.defendant))
        .where(LegalCase.id == case_id)
    )
    case = result.scalar_one_or_none()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    events_result = await db.execute(
        select(LegalCaseEvent)
        .where(LegalCaseEvent.legal_case_id == case.id)
        .order_by(LegalCaseEvent.event_date.desc(), LegalCaseEvent.created_at.desc())
    )
    events = events_result.scalars().all()
    event_ids = [event.id for event in events]
    files_map = {}
    if event_ids:
        files_result = await db.execute(
            select(LegalCaseEventFile).where(LegalCaseEventFile.event_id.in_(event_ids))
        )
        for file_item in files_result.scalars().all():
            files_map.setdefault(file_item.event_id, []).append(file_item)

    tasks_result = await db.execute(
        select(LegalCaseTask, Task, Deal)
        .join(Task, Task.id == LegalCaseTask.task_id)
        .outerjoin(Deal, Deal.id == Task.deal_id)
        .where(LegalCaseTask.legal_case_id == case.id)
    )
    tasks = [
        LegalCaseTaskResponse(
            id=str(task.id),
            title=task.title,
            status=task.status,
            due_date=task.due_date,
            deal_id=str(task.deal_id) if task.deal_id else None,
            deal_title=deal.title if deal else None,
        )
        for _, task, deal in tasks_result.all()
    ]

    return {
        "id": str(case.id),
        "case_number": case.case_number,
        "judge": case.judge,
        "jurisdiction": case.jurisdiction,
        "judge_assistant": case.judge_assistant,
        "judge_assistant_phone": case.judge_assistant_phone,
        "plaintiff_id": case.plaintiff_id,
        "defendant_id": case.defendant_id,
        "plaintiff_name": case.plaintiff.name if case.plaintiff else None,
        "defendant_name": case.defendant.name if case.defendant else None,
        "description": case.description,
        "events": [
            LegalCaseEventResponse(
                id=str(event.id),
                legal_case_id=str(event.legal_case_id),
                event_type=event.event_type,
                event_date=event.event_date,
                event_time=event.event_time,
                courtroom=event.courtroom,
                files=[
                    LegalCaseEventFileResponse(
                        id=str(file_item.id),
                        event_id=str(file_item.event_id),
                        file_name=file_item.file_name,
                        storage_path=file_item.storage_path or file_item.yandex_path,
                        created_at=file_item.created_at,
                    )
                    for file_item in files_map.get(event.id, [])
                ],
                created_at=event.created_at,
            )
            for event in events
        ],
        "tasks": tasks,
        "created_at": case.created_at,
        "updated_at": case.updated_at,
    }


@router.post("/", response_model=LegalCaseResponse)
async def create_legal_case(payload: LegalCaseCreate, db: AsyncSession = Depends(get_db)):
    await _ensure_company(db, payload.plaintiff_id, "plaintiff")
    await _ensure_company(db, payload.defendant_id, "defendant")
    case = await LegalCase.create(db, **payload.dict(exclude_unset=True))
    return {
        "id": str(case.id),
        "case_number": case.case_number,
        "judge": case.judge,
        "jurisdiction": case.jurisdiction,
        "judge_assistant": case.judge_assistant,
        "judge_assistant_phone": case.judge_assistant_phone,
        "plaintiff_id": case.plaintiff_id,
        "defendant_id": case.defendant_id,
        "plaintiff_name": None,
        "defendant_name": None,
        "description": case.description,
        "events": [],
        "tasks": [],
        "created_at": case.created_at,
        "updated_at": case.updated_at,
    }


@router.put("/{case_id}", response_model=LegalCaseResponse)
async def update_legal_case(case_id: str, payload: LegalCaseUpdate, db: AsyncSession = Depends(get_db)):
    case = await LegalCase.get_by_id(db, case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    if payload.plaintiff_id is not None:
        await _ensure_company(db, payload.plaintiff_id, "plaintiff")
    if payload.defendant_id is not None:
        await _ensure_company(db, payload.defendant_id, "defendant")
    updated = await LegalCase.update(db, case_id, **payload.dict(exclude_unset=True))
    return {
        "id": str(updated.id),
        "case_number": updated.case_number,
        "judge": updated.judge,
        "jurisdiction": updated.jurisdiction,
        "judge_assistant": updated.judge_assistant,
        "judge_assistant_phone": updated.judge_assistant_phone,
        "plaintiff_id": updated.plaintiff_id,
        "defendant_id": updated.defendant_id,
        "plaintiff_name": None,
        "defendant_name": None,
        "description": updated.description,
        "events": [],
        "tasks": [],
        "created_at": updated.created_at,
        "updated_at": updated.updated_at,
    }


@router.delete("/{case_id}")
async def delete_legal_case(case_id: str, db: AsyncSession = Depends(get_db)):
    case = await LegalCase.get_by_id(db, case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    event_ids = await db.execute(
        select(LegalCaseEvent.id).where(LegalCaseEvent.legal_case_id == case_id)
    )
    event_id_list = [row[0] for row in event_ids.all()]
    if event_id_list:
        await db.execute(delete(LegalCaseEventFile).where(LegalCaseEventFile.event_id.in_(event_id_list)))
    await db.execute(delete(LegalCaseEvent).where(LegalCaseEvent.legal_case_id == case_id))
    await db.execute(delete(LegalCaseTask).where(LegalCaseTask.legal_case_id == case_id))
    await db.commit()
    await LegalCase.delete(db, case_id)
    return {"message": "Case deleted"}


@router.post("/{case_id}/events", response_model=LegalCaseEventResponse)
async def create_event(case_id: str, payload: LegalCaseEventCreate, db: AsyncSession = Depends(get_db)):
    if payload.event_type not in EVENT_TYPES:
        raise HTTPException(status_code=400, detail="Unknown event type")
    case = await LegalCase.get_by_id(db, case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    event = await LegalCaseEvent.create(db, legal_case_id=case.id, **payload.dict())
    return LegalCaseEventResponse(
        id=str(event.id),
        legal_case_id=str(event.legal_case_id),
        event_type=event.event_type,
        event_date=event.event_date,
        event_time=event.event_time,
        courtroom=event.courtroom,
        files=[],
        created_at=event.created_at,
    )


@router.put("/events/{event_id}", response_model=LegalCaseEventResponse)
async def update_event(event_id: str, payload: LegalCaseEventUpdate, db: AsyncSession = Depends(get_db)):
    if payload.event_type is not None and payload.event_type not in EVENT_TYPES:
        raise HTTPException(status_code=400, detail="Unknown event type")
    event = await LegalCaseEvent.get_by_id(db, event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    updated = await LegalCaseEvent.update(db, event_id, **payload.dict(exclude_unset=True))
    return LegalCaseEventResponse(
        id=str(updated.id),
        legal_case_id=str(updated.legal_case_id),
        event_type=updated.event_type,
        event_date=updated.event_date,
        event_time=updated.event_time,
        courtroom=updated.courtroom,
        files=[],
        created_at=updated.created_at,
    )


@router.delete("/events/{event_id}")
async def delete_event(event_id: str, db: AsyncSession = Depends(get_db)):
    event = await LegalCaseEvent.get_by_id(db, event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    files_result = await db.execute(
        select(LegalCaseEventFile).where(LegalCaseEventFile.event_id == event_id)
    )
    files = files_result.scalars().all()
    if storage_available():
        for file_item in files:
            try:
                await delete_path(file_item.storage_path)
            except Exception:
                pass
    await db.execute(delete(LegalCaseEventFile).where(LegalCaseEventFile.event_id == event_id))
    await LegalCaseEvent.delete(db, event_id)
    return {"message": "Event deleted"}


@router.post("/events/{event_id}/files/upload", response_model=List[LegalCaseEventFileResponse])
async def upload_event_files(
    event_id: str,
    files: List[UploadFile] = File(...),
    db: AsyncSession = Depends(get_db)
):
    if not storage_available():
        raise HTTPException(status_code=500, detail="Storage is not configured")
    event = await LegalCaseEvent.get_by_id(db, event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    case = await LegalCase.get_by_id(db, event.legal_case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    target_path = _legal_event_storage_path(case, event)
    await ensure_path(target_path)
    created = []
    for upload in files:
        content = await upload.read()
        safe_name = clean_name(upload.filename)
        file_path = f"{target_path}/{safe_name}"
        await upload_bytes_with_safe_extension(file_path, content)
        file_record = LegalCaseEventFile(
            event_id=str(event.id),
            file_name=safe_name,
            yandex_path=file_path,
            storage_path=file_path,
        )
        db.add(file_record)
        created.append(file_record)
    await db.commit()
    for file_record in created:
        await db.refresh(file_record)
    return [
        LegalCaseEventFileResponse(
            id=str(file_record.id),
            event_id=str(file_record.event_id),
            file_name=file_record.file_name,
            storage_path=file_record.storage_path or file_record.yandex_path,
            created_at=file_record.created_at,
        )
        for file_record in created
    ]


@router.get("/events/files/{file_id}/download")
async def download_event_file(file_id: str, db: AsyncSession = Depends(get_db)):
    file_record = await LegalCaseEventFile.get_by_id(db, file_id)
    if not file_record:
        raise HTTPException(status_code=404, detail="File not found")
    if not storage_available():
        raise HTTPException(status_code=500, detail="Storage is not configured")
    try:
        href = await get_download_href(file_record.storage_path or file_record.yandex_path)
    except httpx.HTTPStatusError as exc:
        status = exc.response.status_code
        if status in {404, 410}:
            raise HTTPException(status_code=404, detail="File not found in storage")
        raise HTTPException(status_code=502, detail="Failed to resolve storage download link")
    except Exception:
        raise HTTPException(status_code=502, detail="Failed to resolve storage download link")
    return {"href": href}


@router.delete("/events/files/{file_id}")
async def delete_event_file(file_id: str, db: AsyncSession = Depends(get_db)):
    file_record = await LegalCaseEventFile.get_by_id(db, file_id)
    if not file_record:
        raise HTTPException(status_code=404, detail="File not found")
    if storage_available():
        try:
            await delete_path(file_record.storage_path or file_record.yandex_path)
        except Exception:
            pass
    await db.execute(delete(LegalCaseEventFile).where(LegalCaseEventFile.id == file_id))
    await db.commit()
    return {"message": "File deleted"}


@router.post("/{case_id}/tasks/link", response_model=LegalCaseTaskResponse)
async def link_task(case_id: str, payload: LegalCaseTaskLinkCreate, db: AsyncSession = Depends(get_db)):
    case = await LegalCase.get_by_id(db, case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    task = await Task.get_by_id(db, payload.task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    existing = await db.execute(
        select(LegalCaseTask).where(
            LegalCaseTask.legal_case_id == case.id,
            LegalCaseTask.task_id == task.id,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Task already linked")
    link = LegalCaseTask(legal_case_id=case.id, task_id=task.id)
    db.add(link)
    await db.commit()
    return LegalCaseTaskResponse(
        id=str(task.id),
        title=task.title,
        status=task.status,
        due_date=task.due_date,
        deal_id=str(task.deal_id) if task.deal_id else None,
        deal_title=None,
    )


@router.delete("/{case_id}/tasks/{task_id}")
async def unlink_task(case_id: str, task_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        delete(LegalCaseTask).where(
            LegalCaseTask.legal_case_id == case_id,
            LegalCaseTask.task_id == task_id,
        )
    )
    await db.commit()
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Task link not found")
    return {"message": "Task unlinked"}
