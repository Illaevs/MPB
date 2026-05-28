"""
Bootstrap helpers for document template schema and permissions.
"""
from __future__ import annotations

import uuid
from pathlib import Path

from sqlalchemy import inspect, text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.database.base import Base
from app.database.session import engine_sync
from app.models.document_template import DocumentTemplate, DocumentTemplateVersion
from app.services.document_template_fields import extract_docx_placeholders, unknown_placeholder_keys
from app.services.storage import clean_name


DOCUMENT_TEMPLATES_SECTION_KEY = "document_templates"
PROJECT_ROOT = Path(__file__).resolve().parents[3]
LEGACY_TEMPLATES_DIR = PROJECT_ROOT / "frontend" / "public" / "templates"
LEGACY_OUTGOING_TEMPLATES = {
    "normbud": ("outgoing_normbud.docx", "Письмо НОРМБУД"),
    "bayer": ("outgoing_bayer.docx", "Письмо БАЙЕР"),
    "morozov": ("outgoing_morozov.docx", "Письмо ИП Морозов"),
}


def _legacy_template_storage_path(company_key: str, file_name: str) -> str:
    root = Path(settings.STORAGE_LOCAL_ROOT or "").expanduser()
    safe_name = clean_name(file_name or "template.docx")
    return str(root / "document-templates" / "legacy-outgoing" / company_key / "v1" / safe_name)


def _ensure_legacy_outgoing_templates() -> None:
    if not settings.STORAGE_LOCAL_ROOT:
        return
    with Session(engine_sync) as session:
        for company_key, (file_name, label) in LEGACY_OUTGOING_TEMPLATES.items():
            source = LEGACY_TEMPLATES_DIR / file_name
            if not source.exists():
                continue
            existing = session.execute(
                text(
                    """
                    SELECT id
                    FROM document_templates
                    WHERE module = 'outgoing_registry'
                      AND document_kind = 'letter'
                      AND our_company_key = :company_key
                      AND binding_type = 'company'
                    LIMIT 1
                    """
                ),
                {"company_key": company_key},
            ).fetchone()
            if existing:
                continue
            content = source.read_bytes()
            placeholders = extract_docx_placeholders(content)
            unknown_fields = unknown_placeholder_keys(placeholders)
            template = DocumentTemplate(
                name=label,
                description="Импортирован из старых статических шаблонов писем.",
                module="outgoing_registry",
                document_kind="letter",
                our_company_key=company_key,
                binding_type="company",
                binding_id=None,
                status="approved",
                is_active=True,
                fields_json=placeholders,
                unknown_fields_json=unknown_fields,
                created_by="bootstrap",
                updated_by="bootstrap",
            )
            session.add(template)
            session.flush()
            target = Path(_legacy_template_storage_path(company_key, file_name))
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(content)
            version = DocumentTemplateVersion(
                template_id=str(template.id),
                version_number=1,
                file_name=clean_name(file_name),
                file_path=str(target),
                file_size=len(content),
                content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                fields_json=placeholders,
                unknown_fields_json=unknown_fields,
                created_by="bootstrap",
            )
            session.add(version)
            session.flush()
            template.current_version_id = str(version.id)
        session.commit()


def ensure_document_templates_schema() -> None:
    Base.metadata.create_all(
        engine_sync,
        tables=[DocumentTemplate.__table__, DocumentTemplateVersion.__table__],
    )
    _ensure_legacy_outgoing_templates()
    inspector = inspect(engine_sync)
    if not inspector.has_table("roles") or not inspector.has_table("role_permissions"):
        return

    with engine_sync.begin() as connection:
        system_roles = connection.execute(
            text("SELECT id FROM roles WHERE is_system = 1")
        ).fetchall()
        for system_role in system_roles:
            role_id = str(system_role[0])
            existing = connection.execute(
                text(
                    """
                    SELECT id
                    FROM role_permissions
                    WHERE role_id = :role_id AND section = :section
                    LIMIT 1
                    """
                ),
                {"role_id": role_id, "section": DOCUMENT_TEMPLATES_SECTION_KEY},
            ).fetchone()
            if existing:
                connection.execute(
                    text(
                        """
                        UPDATE role_permissions
                        SET read_all = 1,
                            read_assigned = 1
                        WHERE id = :permission_id
                        """
                    ),
                    {"permission_id": str(existing[0])},
                )
            else:
                connection.execute(
                    text(
                        """
                        INSERT INTO role_permissions (id, role_id, section, read_all, read_assigned)
                        VALUES (:id, :role_id, :section, 1, 1)
                        """
                    ),
                    {
                        "id": str(uuid.uuid4()),
                        "role_id": role_id,
                        "section": DOCUMENT_TEMPLATES_SECTION_KEY,
                    },
                )
