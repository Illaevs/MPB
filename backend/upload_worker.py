#!/usr/bin/env python3
"""
Background worker for processing upload queue jobs.
"""
import asyncio
from datetime import datetime, timedelta
from pathlib import Path

from sqlalchemy import select, or_

from app.core.config import settings
from app.database.session import async_session
from app.models import (
    UploadJob,
    ContractDocument,
    DocumentDispatchChannel,
    CompanyDocument,
    LegalCaseEventFile,
    OutgoingDocumentFile,
    StageResult,
    KpVersion,
)
from app.services.storage import ensure_path, publish, upload_file_with_safe_extension_sync, storage_available
from app.services.event_log import log_event


def _tmp_dir() -> Path:
    if settings.UPLOAD_TMP_DIR:
        return Path(settings.UPLOAD_TMP_DIR)
    base = Path(__file__).resolve().parents[1]
    return base / "tmp_uploads"


async def _mark_error(db, job: UploadJob, message: str):
    try:
        await db.rollback()
    except Exception:
        pass

    persisted_job = await db.get(UploadJob, str(job.id))
    if not persisted_job:
        return

    persisted_job.status = "error"
    persisted_job.error_message = message[:500] if message else "Unknown error"
    await db.commit()
    try:
        await log_event(
            db,
            entity_type="upload",
            entity_id=str(persisted_job.id),
            action="upload.error",
            details={
                "error_message": persisted_job.error_message,
                "module": persisted_job.module,
                "file_name": persisted_job.file_name,
                "entity_id": persisted_job.entity_id,
            },
            created_by=str(persisted_job.created_by or ""),
        )
    except Exception:
        pass


async def _process_job(db, job: UploadJob) -> None:
    if not storage_available():
        await _mark_error(db, job, "Storage is not configured")
        return
    if not job.temp_path:
        await _mark_error(db, job, "Temp file is missing")
        return

    temp_path = Path(job.temp_path)
    if not temp_path.exists():
        await _mark_error(db, job, "Temp file not found")
        return

    try:
        job.status = "processing"
        await db.commit()

        target_path = job.target_path
        if not target_path:
            raise RuntimeError("Target path is missing")

        folder_path = target_path.rsplit("/", 1)[0]
        await ensure_path(folder_path)
        await asyncio.to_thread(upload_file_with_safe_extension_sync, target_path, str(temp_path))

        if job.module == "contracts":
            document_id = (job.meta or {}).get("document_id")
            file_kind = job.file_kind
            if document_id and file_kind:
                # Upload audit: use the display-name snapshot captured at enqueue
                # time (meta.uploaded_by); the file lands now, so stamp time now.
                uploaded_by = (job.meta or {}).get("uploaded_by")
                uploaded_at = datetime.now()
                update_payload = {}
                if file_kind == "pdf":
                    update_payload["pdf_file_name"] = job.file_name
                    update_payload["pdf_storage_path"] = target_path
                    update_payload["pdf_uploaded_by"] = uploaded_by
                    update_payload["pdf_uploaded_at"] = uploaded_at
                else:
                    update_payload["edit_file_name"] = job.file_name
                    update_payload["edit_storage_path"] = target_path
                    update_payload["edit_uploaded_by"] = uploaded_by
                    update_payload["edit_uploaded_at"] = uploaded_at
                await ContractDocument.update(db, document_id, **update_payload)
        elif job.module == "document_registry":
            channel_id = (job.meta or {}).get("channel_id")
            channel_folder = (job.meta or {}).get("channel_folder") or folder_path
            if channel_id:
                result = await db.execute(
                    select(DocumentDispatchChannel).where(DocumentDispatchChannel.id == channel_id)
                )
                channel = result.scalar_one_or_none()
                if channel and channel.confirmation_file != channel_folder:
                    channel.confirmation_file = channel_folder
                    await db.commit()
        elif job.module == "accreditations":
            meta = job.meta or {}
            company_id = meta.get("company_id")
            doc_type = meta.get("doc_type")
            doc_value = meta.get("doc_value")
            parent_id = meta.get("parent_id")
            if company_id and doc_type:
                file_name = target_path.rsplit("/", 1)[-1]
                doc = CompanyDocument(
                    company_id=company_id,
                    doc_type=doc_type,
                    doc_value=doc_value,
                    file_name=file_name,
                    storage_path=target_path,
                    parent_id=parent_id,
                    status="pending",
                )
                db.add(doc)
                await db.commit()
        elif job.module == "legal_work":
            meta = job.meta or {}
            event_id = meta.get("event_id")
            if event_id:
                file_name = meta.get("file_name") or target_path.rsplit("/", 1)[-1]
                existing_result = await db.execute(
                    select(LegalCaseEventFile).where(
                        LegalCaseEventFile.event_id == event_id,
                        or_(
                            LegalCaseEventFile.storage_path == target_path,
                            LegalCaseEventFile.yandex_path == target_path,
                        ),
                    )
                )
                existing = existing_result.scalar_one_or_none()
                if not existing:
                    file_record = LegalCaseEventFile(
                        event_id=event_id,
                        file_name=file_name,
                        yandex_path=target_path,
                        storage_path=target_path,
                    )
                    db.add(file_record)
                    await db.commit()
        elif job.module == "outgoing_registry":
            meta = job.meta or {}
            document_id = meta.get("document_id")
            if document_id:
                file_name = meta.get("file_name") or target_path.rsplit("/", 1)[-1]
                public_url = await publish(target_path)
                await OutgoingDocumentFile.create(
                    db,
                    document_id=document_id,
                    file_type="attachment",
                    file_path=target_path,
                    file_name=file_name,
                    public_url=public_url,
                )
        elif job.module == "executor_results":
            meta = job.meta or {}
            result_id = meta.get("stage_result_id")
            version_path = meta.get("version_path") or folder_path
            if result_id:
                result = await StageResult.get_by_id(db, result_id)
                if result and not result.public_url:
                    result.public_url = await publish(version_path)
                    result.updated_at = datetime.utcnow()
                    await db.commit()
        elif job.module == "kp":
            meta = job.meta or {}
            version_id = meta.get("version_id")
            is_pdf = bool(meta.get("is_pdf"))
            if version_id:
                result = await db.execute(select(KpVersion).where(KpVersion.id == version_id))
                version = result.scalar_one_or_none()
                if version:
                    url = await publish(target_path)
                    if is_pdf:
                        version.pdf_url = url
                    else:
                        version.docx_url = url
                    await db.commit()

        job.status = "done"
        job.error_message = None
        await db.commit()

        temp_path.unlink(missing_ok=True)
    except Exception as exc:
        await _mark_error(db, job, str(exc))


async def _cleanup_temp_files():
    tmp_dir = _tmp_dir()
    if not tmp_dir.exists():
        return
    ttl_hours = settings.UPLOAD_TMP_TTL_HOURS or 24
    cutoff = datetime.utcnow() - timedelta(hours=ttl_hours)
    for file_path in tmp_dir.iterdir():
        if not file_path.is_file():
            continue
        try:
            if datetime.utcfromtimestamp(file_path.stat().st_mtime) < cutoff:
                file_path.unlink(missing_ok=True)
        except Exception:
            continue


async def run_loop():
    while True:
        async with async_session() as db:
            result = await db.execute(
                select(UploadJob).where(UploadJob.status == "queued").order_by(UploadJob.created_at.asc()).limit(5)
            )
            jobs = result.scalars().all()
            for job in jobs:
                await _process_job(db, job)
        await _cleanup_temp_files()
        await asyncio.sleep(3)


if __name__ == "__main__":
    asyncio.run(run_loop())
