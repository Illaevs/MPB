from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.core.auth_middleware import CurrentUser
from app.models import User
from app.schemas.data_health import (
    DataHealthDealCountsResponse,
    DataHealthGroupedListResponse,
    DataHealthIgnoreRequest,
    DataHealthIssueResponse,
    DataHealthListResponse,
)
from app.services.data_health import (
    get_deal_health_counts,
    get_grouped_health_issues,
    get_health_issues,
    refresh_all_health_issues,
    refresh_deal_health_issues,
    refresh_orphan_health_issues,
    set_health_issue_status,
)
from app.services.data_health_report import build_data_health_report_pdf


router = APIRouter()


def _issue_response(issue, navigation_path=None, navigation_query=None):
    return DataHealthIssueResponse(
        id=issue.id,
        fingerprint=issue.fingerprint,
        deal_id=issue.deal_id,
        deal_title=None,
        scope_type=issue.scope_type,
        scope_id=issue.scope_id,
        issue_type=issue.issue_type,
        module=issue.module,
        severity=issue.severity,
        status=issue.status,
        title=issue.title,
        description=issue.description or "",
        payload=issue.payload_json or {},
        navigation_path=navigation_path,
        navigation_query=navigation_query or {},
        first_detected_at=issue.first_detected_at,
        last_detected_at=issue.last_detected_at,
        resolved_at=issue.resolved_at,
        ignored_reason=issue.ignored_reason,
        ignored_until=issue.ignored_until,
        ignored_by_user_id=issue.ignored_by_user_id,
        ignored_at=issue.ignored_at,
    )


@router.get("/issues", response_model=DataHealthListResponse)
async def list_health_issues(
    refresh: bool = Query(False),
    deal_id: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    issue_type: Optional[str] = Query(None),
    module: Optional[str] = Query(None),
    status: str = Query("active"),
    search: Optional[str] = Query(None),
    offset: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
):
    if refresh:
        if deal_id:
            await refresh_deal_health_issues(db, deal_id)
        else:
            await refresh_all_health_issues(db)
    return await get_health_issues(
        db,
        deal_id=deal_id,
        severity=severity,
        issue_type=issue_type,
        module=module,
        status=status,
        search=search,
        offset=offset,
        limit=limit,
    )


@router.get("/issues/groups", response_model=DataHealthGroupedListResponse)
async def list_grouped_health_issues(
    refresh: bool = Query(False),
    deal_id: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    issue_type: Optional[str] = Query(None),
    module: Optional[str] = Query(None),
    status: str = Query("active"),
    search: Optional[str] = Query(None),
    offset: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
):
    if refresh:
        if deal_id:
            await refresh_deal_health_issues(db, deal_id)
        else:
            await refresh_all_health_issues(db)
    return await get_grouped_health_issues(
        db,
        deal_id=deal_id,
        severity=severity,
        issue_type=issue_type,
        module=module,
        status=status,
        search=search,
        offset=offset,
        limit=limit,
    )


@router.get("/report.pdf")
async def download_health_report_pdf(
    refresh: bool = Query(False),
    deal_id: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    issue_type: Optional[str] = Query(None),
    module: Optional[str] = Query(None),
    status: str = Query("active"),
    search: Optional[str] = Query(None),
    grouped: bool = Query(True),
    db: AsyncSession = Depends(get_db),
):
    if refresh:
        if deal_id:
            await refresh_deal_health_issues(db, deal_id)
        else:
            await refresh_all_health_issues(db)
    pdf_bytes = await build_data_health_report_pdf(
        db,
        deal_id=deal_id,
        severity=severity,
        issue_type=issue_type,
        module=module,
        status=status,
        search=search,
        grouped=grouped,
    )
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": 'attachment; filename="data-health-report.pdf"'},
    )


@router.get("/deal-counts", response_model=DataHealthDealCountsResponse)
async def list_deal_health_counts(
    refresh: bool = Query(False),
    deal_ids: Optional[list[str]] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    if refresh:
        if deal_ids:
            for deal_id in deal_ids:
                await refresh_deal_health_issues(db, deal_id)
        else:
            await refresh_all_health_issues(db)
    return {"items": await get_deal_health_counts(db, deal_ids=deal_ids)}


@router.get("/deals/{deal_id}/issues", response_model=DataHealthListResponse)
async def list_deal_health_issues(
    deal_id: str,
    refresh: bool = Query(True),
    severity: Optional[str] = Query(None),
    issue_type: Optional[str] = Query(None),
    module: Optional[str] = Query(None),
    status: str = Query("active"),
    search: Optional[str] = Query(None),
    offset: int = Query(0, ge=0),
    limit: int = Query(200, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
):
    if refresh:
        await refresh_deal_health_issues(db, deal_id)
    return await get_health_issues(
        db,
        deal_id=deal_id,
        severity=severity,
        issue_type=issue_type,
        module=module,
        status=status,
        search=search,
        offset=offset,
        limit=limit,
    )


@router.post("/refresh", response_model=DataHealthListResponse)
async def refresh_health_issues(
    deal_id: Optional[str] = Query(None),
    orphan_only: bool = Query(False),
    db: AsyncSession = Depends(get_db),
):
    if orphan_only:
        await refresh_orphan_health_issues(db)
    elif deal_id:
        await refresh_deal_health_issues(db, deal_id)
    else:
        await refresh_all_health_issues(db)
    return await get_health_issues(db, deal_id=deal_id, status="active", offset=0, limit=100)


@router.post("/issues/{issue_id}/ignore", response_model=DataHealthIssueResponse)
async def ignore_health_issue(
    issue_id: str,
    payload: DataHealthIgnoreRequest | None = None,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(CurrentUser),
):
    payload = payload or DataHealthIgnoreRequest()
    issue = await set_health_issue_status(
        db,
        issue_id,
        "ignored",
        ignored_reason=payload.reason,
        ignored_until=payload.ignored_until,
        ignored_by_user_id=str(user.id),
    )
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")
    return _issue_response(issue)


@router.post("/issues/{issue_id}/open", response_model=DataHealthIssueResponse)
async def reopen_health_issue(issue_id: str, db: AsyncSession = Depends(get_db)):
    issue = await set_health_issue_status(db, issue_id, "open")
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")
    return _issue_response(issue)
