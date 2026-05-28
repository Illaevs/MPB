from __future__ import annotations

import asyncio
import os
import re
import shutil
import sys
import uuid
import zipfile
from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

from sqlalchemy import UUID as SAUUID
from sqlalchemy.ext.compiler import compiles


REPO_ROOT = Path(__file__).resolve().parents[2]
BACKEND_DIR = REPO_ROOT / "backend"
TEST_ROOT = REPO_ROOT / "test_portal"
DB_PATH = TEST_ROOT / "crm_test_portal.db"
STORAGE_ROOT = TEST_ROOT / "storage"
STATIC_ROOT = TEST_ROOT / "static"
TMP_ROOT = TEST_ROOT / "tmp_uploads"
README_PATH = TEST_ROOT / "README.md"

MAIN_DB_CANDIDATES = [
    REPO_ROOT / "crm.db",
    BACKEND_DIR / "crm.db",
]

TEST_SECRET_KEY = "testportal-nexus-secret-key-should-be-long-and-isolated-2026-local-only-0123456789"


@compiles(SAUUID, "sqlite")
def _compile_uuid_sqlite(_type, _compiler, **_kw) -> str:
    return "CHAR(36)"


_original_uuid_bind_processor = SAUUID.bind_processor


def _patched_uuid_bind_processor(self, dialect):
    processor = _original_uuid_bind_processor(self, dialect)
    if processor is None:
        return None

    def process(value):
        if isinstance(value, str):
            try:
                value = uuid.UUID(value)
            except (ValueError, TypeError):
                pass
        return processor(value)

    return process


SAUUID.bind_processor = _patched_uuid_bind_processor


def _ensure_backend_on_path() -> None:
    backend_str = str(BACKEND_DIR)
    if backend_str not in sys.path:
        sys.path.insert(0, backend_str)


def _path_signature(path: Path) -> Tuple[bool, int, int]:
    if not path.exists():
        return False, 0, 0
    stat = path.stat()
    return True, stat.st_size, stat.st_mtime_ns


def _assert_safe_test_root(path: Path) -> None:
    resolved = path.resolve()
    if resolved.name != "test_portal":
        raise RuntimeError(f"Unsafe test portal root: {resolved}")
    if REPO_ROOT.resolve() not in resolved.parents:
        raise RuntimeError(f"Test portal root escaped repository: {resolved}")


def _prepare_test_root() -> None:
    _assert_safe_test_root(TEST_ROOT)
    if TEST_ROOT.exists():
        shutil.rmtree(TEST_ROOT)
    for directory in (TEST_ROOT, STORAGE_ROOT, STATIC_ROOT, TMP_ROOT, STATIC_ROOT / "avatars"):
        directory.mkdir(parents=True, exist_ok=True)


def _set_test_env() -> None:
    env = {
        "APP_VARIANT": "test_portal",
        "SECRET_KEY": TEST_SECRET_KEY,
        "SQLALCHEMY_DATABASE_URI": f"sqlite:///{DB_PATH.as_posix()}",
        "STORAGE_BACKEND": "local",
        "STORAGE_LOCAL_ROOT": STORAGE_ROOT.as_posix(),
        "STATIC_LOCAL_ROOT": STATIC_ROOT.as_posix(),
        "UPLOAD_TMP_DIR": TMP_ROOT.as_posix(),
        "AUTH_COOKIE_SECURE": "false",
        "TWO_FACTOR_ISSUER": "Nexus",
        "APP_HOST": "127.0.0.1",
        "APP_PORT": "8001",
        "APP_RELOAD": "false",
        "REDIS_URL": "",
    }
    for key, value in env.items():
        os.environ[key] = value


_assert_safe_test_root(TEST_ROOT)
_ensure_backend_on_path()
_set_test_env()

from sqlalchemy.orm import sessionmaker  # noqa: E402

from app.core.security import hash_password  # noqa: E402
from app.database.base import Base  # noqa: E402
from app.database.session import engine_sync  # noqa: E402
from app.models import (  # noqa: E402
    AuditLog,
    CBRate,
    ChatConversation,
    ChatConversationMember,
    Company,
    CompanyAccreditation,
    CompanyDocument,
    CompanyUserLink,
    Contract,
    ContractDocument,
    Deal,
    DealGip,
    DealProduct,
    Document,
    DocumentDispatch,
    DocumentDispatchChannel,
    DocumentPackage,
    DocumentPackageItem,
    DocumentRelation,
    EventLog,
    FinancialPlan,
    GlobalChatMessage,
    IncomeExpenseEntry,
    KpDocument,
    KpTemplate,
    KpTemplateBinding,
    KpVersion,
    Lead,
    LeadProduct,
    LegalCase,
    LegalCaseEvent,
    LegalCaseEventFile,
    LegalCaseTask,
    MailMessage,
    Mailbox,
    Notification,
    NotificationJob,
    NotificationPreference,
    NotificationRule,
    NotificationSubscription,
    OutgoingDocument,
    OutgoingDocumentFile,
    OutgoingDocumentVersion,
    OutgoingNumberSequence,
    PenaltyRule,
    Product,
    ProductCategory,
    Role,
    RolePermission,
    Stage,
    StageDependency,
    StageProductAssignment,
    StageProductLink,
    StageProductSubtask,
    StageResult,
    SubcontractorCard,
    SubcontractorProduct,
    SubcontractorStage,
    SubcontractorStageDependency,
    Task,
    TaskAuction,
    TaskAuctionBid,
    TaskMessage,
    Tender,
    TenderOffer,
    TransactionAllocation,
    TreasuryAllocation,
    TreasuryAutoRule,
    TreasuryTransaction,
    UploadJob,
    User,
    WorkResult,
)
from app.services.chat_bootstrap import ensure_chat_schema  # noqa: E402
from app.services.customer_portal_bootstrap import (  # noqa: E402
    CUSTOMER_ROLE_NAME,
    ensure_customer_portal_role,
)
from app.services.permissions import AUTHENTICATED_SECTION_KEYS  # noqa: E402
from app.services.stage_product_assignment_bootstrap import (  # noqa: E402
    ensure_stage_product_assignment_schema,
)
from app.services.user_avatar_bootstrap import ensure_user_avatar_schema  # noqa: E402
from app.services.user_two_factor_bootstrap import ensure_user_two_factor_schema  # noqa: E402


SessionLocal = sessionmaker(bind=engine_sync, autoflush=False, expire_on_commit=False)


def storage_rel(*parts: str) -> str:
    cleaned = [str(part).strip("/\\") for part in parts if str(part).strip("/\\")]
    return "/" + "/".join(cleaned)


def storage_abs(rel_path: str) -> Path:
    return STORAGE_ROOT / rel_path.lstrip("/").replace("/", os.sep)


def write_abs_bytes(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)


def write_abs_text(path: Path, text: str) -> None:
    write_abs_bytes(path, text.encode("utf-8"))


def _escape_pdf_text(value: str) -> str:
    return value.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def write_storage_bytes(rel_path: str, payload: bytes) -> str:
    path = storage_abs(rel_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)
    return rel_path


def write_storage_text(rel_path: str, text: str) -> str:
    return write_storage_bytes(rel_path, text.encode("utf-8"))


def make_pdf_bytes(title: str, lines: Iterable[str]) -> bytes:
    text_lines = [title, *[line for line in lines if line]]
    stream_lines = ["BT", "/F1 18 Tf", "50 780 Td"]
    for index, line in enumerate(text_lines):
        if index == 1:
            stream_lines.append("/F1 11 Tf")
        escaped = _escape_pdf_text(line)
        stream_lines.append(f"({escaped}) Tj")
        if index != len(text_lines) - 1:
            stream_lines.append("0 -22 Td")
    stream_lines.append("ET")
    stream = "\n".join(stream_lines).encode("latin-1", "replace")
    objects = [
        b"1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj\n",
        b"2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj\n",
        b"3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >> endobj\n",
        b"4 0 obj << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> endobj\n",
        f"5 0 obj << /Length {len(stream)} >> stream\n".encode("ascii") + stream + b"\nendstream endobj\n",
    ]
    result = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for obj in objects:
        offsets.append(len(result))
        result.extend(obj)
    xref_pos = len(result)
    result.extend(f"xref\n0 {len(offsets)}\n".encode("ascii"))
    result.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        result.extend(f"{offset:010d} 00000 n \n".encode("ascii"))
    result.extend(
        f"trailer << /Size {len(offsets)} /Root 1 0 R >>\nstartxref\n{xref_pos}\n%%EOF\n".encode("ascii")
    )
    return bytes(result)


def write_pdf(rel_path: str, title: str, *lines: str) -> str:
    return write_storage_bytes(rel_path, make_pdf_bytes(title, lines))


def make_docx_bytes(title: str, paragraphs: Iterable[str]) -> bytes:
    paragraphs_xml = []
    for paragraph in [title, *[value for value in paragraphs if value]]:
        safe = (
            paragraph.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
        )
        paragraphs_xml.append(
            f"<w:p><w:r><w:t xml:space=\"preserve\">{safe}</w:t></w:r></w:p>"
        )
    document_xml = (
        "<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"yes\"?>"
        "<w:document xmlns:wpc=\"http://schemas.microsoft.com/office/word/2010/wordprocessingCanvas\" "
        "xmlns:mc=\"http://schemas.openxmlformats.org/markup-compatibility/2006\" "
        "xmlns:o=\"urn:schemas-microsoft-com:office:office\" "
        "xmlns:r=\"http://schemas.openxmlformats.org/officeDocument/2006/relationships\" "
        "xmlns:m=\"http://schemas.openxmlformats.org/officeDocument/2006/math\" "
        "xmlns:v=\"urn:schemas-microsoft-com:vml\" "
        "xmlns:wp14=\"http://schemas.microsoft.com/office/word/2010/wordprocessingDrawing\" "
        "xmlns:wp=\"http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing\" "
        "xmlns:w10=\"urn:schemas-microsoft-com:office:word\" "
        "xmlns:w=\"http://schemas.openxmlformats.org/wordprocessingml/2006/main\" "
        "xmlns:w14=\"http://schemas.microsoft.com/office/word/2010/wordml\" "
        "xmlns:wpg=\"http://schemas.microsoft.com/office/word/2010/wordprocessingGroup\" "
        "xmlns:wpi=\"http://schemas.microsoft.com/office/word/2010/wordprocessingInk\" "
        "xmlns:wne=\"http://schemas.microsoft.com/office/2006/wordml\" "
        "xmlns:wps=\"http://schemas.microsoft.com/office/word/2010/wordprocessingShape\" "
        "mc:Ignorable=\"w14 wp14\">"
        f"<w:body>{''.join(paragraphs_xml)}<w:sectPr><w:pgSz w:w=\"11906\" w:h=\"16838\"/>"
        "<w:pgMar w:top=\"1440\" w:right=\"1440\" w:bottom=\"1440\" w:left=\"1440\" "
        "w:header=\"708\" w:footer=\"708\" w:gutter=\"0\"/></w:sectPr></w:body></w:document>"
    )
    content_types = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
</Types>"""
    root_rels = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
</Relationships>"""
    buffer = Path(TEST_ROOT / "_docx_buffer.zip")
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", content_types)
        archive.writestr("_rels/.rels", root_rels)
        archive.writestr("word/document.xml", document_xml)
    payload = buffer.read_bytes()
    buffer.unlink(missing_ok=True)
    return payload


def write_docx(rel_path: str, title: str, *paragraphs: str) -> str:
    return write_storage_bytes(rel_path, make_docx_bytes(title, paragraphs))


def clean_name(value: str) -> str:
    normalized = re.sub(r"[\\/:*?\"<>|]+", " ", value).strip()
    return re.sub(r"\s+", " ", normalized)


def local_entity_roots(entity_id: str, title: str) -> Dict[str, Path]:
    safe_title = clean_name(title or f"Entity {entity_id}")
    return {
        "tz": STORAGE_ROOT / f"[#{entity_id}] {safe_title} (ТЗ)",
        "other": STORAGE_ROOT / f"[#{entity_id}] {safe_title} (Прочее)",
        "results": STORAGE_ROOT / f"[#{entity_id}] {safe_title} (Результаты)",
    }


def money_fields(
    quantity: float,
    unit_price: float,
    tax_rate: float = 20.0,
    discount_percent: float = 0.0,
    discount_amount: float = 0.0,
) -> Dict[str, float]:
    total_price = round(quantity * unit_price, 2)
    discount_from_percent = round(total_price * (discount_percent / 100.0), 2)
    discount_total = round(discount_from_percent + discount_amount, 2)
    subtotal = round(total_price - discount_total, 2)
    tax_amount = round(subtotal * (tax_rate / 100.0), 2)
    final_price = round(subtotal + tax_amount, 2)
    return {
        "quantity": quantity,
        "unit_price": round(unit_price, 2),
        "discount_percent": round(discount_percent, 2),
        "discount_amount": round(discount_amount, 2),
        "total_price": total_price,
        "discount_total": discount_total,
        "tax_rate": round(tax_rate, 2),
        "tax_amount": tax_amount,
        "final_price": final_price,
    }


@dataclass
class SeedState:
    roles: Dict[str, Role] = field(default_factory=dict)
    users: Dict[str, User] = field(default_factory=dict)
    companies: Dict[str, Company] = field(default_factory=dict)
    product_categories: Dict[str, ProductCategory] = field(default_factory=dict)
    products: Dict[str, Product] = field(default_factory=dict)
    leads: Dict[str, Lead] = field(default_factory=dict)
    deals: Dict[str, Deal] = field(default_factory=dict)
    stages: Dict[str, Stage] = field(default_factory=dict)
    deal_products: Dict[str, DealProduct] = field(default_factory=dict)
    contracts: Dict[str, Contract] = field(default_factory=dict)
    subcontractor_cards: Dict[str, SubcontractorCard] = field(default_factory=dict)
    subcontractor_stages: Dict[str, SubcontractorStage] = field(default_factory=dict)
    subcontractor_products: Dict[str, SubcontractorProduct] = field(default_factory=dict)
    assignments: Dict[str, StageProductAssignment] = field(default_factory=dict)
    tasks: Dict[str, Task] = field(default_factory=dict)
    mailboxes: Dict[str, Mailbox] = field(default_factory=dict)
    outgoing_documents: Dict[str, OutgoingDocument] = field(default_factory=dict)
    documents: Dict[str, Document] = field(default_factory=dict)


def _string_id() -> str:
    return str(uuid.uuid4())


def _uuid_id() -> uuid.UUID:
    return uuid.uuid4()


def _uuid_string(value: str | uuid.UUID | None) -> uuid.UUID | None:
    if value in (None, ""):
        return None
    if isinstance(value, uuid.UUID):
        return value
    return uuid.UUID(str(value))


def add_role_with_permissions(
    db,
    *,
    role_id: str,
    name: str,
    description: str,
    is_system: bool,
    read_all_sections: Iterable[str] = (),
    read_assigned_sections: Iterable[str] = (),
) -> Role:
    role = Role(
        id=role_id,
        name=name,
        description=description,
        is_system=is_system,
    )
    db.add(role)
    for section in sorted(set(read_all_sections)):
        db.add(
            RolePermission(
                id=_string_id(),
                role_id=role_id,
                section=section,
                read_all=True,
                read_assigned=False,
            )
        )
    for section in sorted(set(read_assigned_sections)):
        db.add(
            RolePermission(
                id=_string_id(),
                role_id=role_id,
                section=section,
                read_all=False,
                read_assigned=True,
            )
        )
    return role


def bootstrap_database() -> None:
    Base.metadata.create_all(bind=engine_sync)
    ensure_customer_portal_role()
    ensure_user_avatar_schema()
    ensure_user_two_factor_schema()
    ensure_stage_product_assignment_schema()
    asyncio.run(ensure_chat_schema())


def seed_everything() -> SeedState:
    state = SeedState()
    db = SessionLocal()
    try:
        customer_role = db.query(Role).filter(Role.name == CUSTOMER_ROLE_NAME).one()

        state.roles["admin"] = add_role_with_permissions(
            db,
            role_id=_string_id(),
            name="Nexus Администратор",
            description="Полный тестовый доступ ко всем разделам.",
            is_system=True,
            read_all_sections=[*AUTHENTICATED_SECTION_KEYS, "customer_portal"],
        )
        state.roles["manager"] = add_role_with_permissions(
            db,
            role_id=_string_id(),
            name="Nexus Руководитель проекта",
            description="Управление тестовыми проектами и договорами.",
            is_system=False,
            read_all_sections=[
                "projects",
                "leads",
                "companies",
                "contracts",
                "catalog",
                "tasks",
                "task_chat",
                "global_chat",
                "calendar",
                "legal_work",
                "finance",
                "treasury",
                "income_expense",
                "executor",
                "outgoing_registry",
                "document_registry",
                "files_catalog",
                "mail",
                "work_results_reviews",
                "tenders_admin",
                "accreditations_admin",
            ],
            read_assigned_sections=["customer_portal"],
        )
        state.roles["finance"] = add_role_with_permissions(
            db,
            role_id=_string_id(),
            name="Nexus Финансы",
            description="Тестовый финансовый контур.",
            is_system=False,
            read_all_sections=["finance", "treasury", "income_expense", "contracts", "projects", "companies", "catalog"],
        )
        state.roles["contracts"] = add_role_with_permissions(
            db,
            role_id=_string_id(),
            name="Nexus Договорной отдел",
            description="Контрактация и исходящие письма.",
            is_system=False,
            read_all_sections=["contracts", "projects", "companies", "outgoing_registry", "document_registry", "files_catalog", "mail"],
        )
        state.roles["executor"] = add_role_with_permissions(
            db,
            role_id=_string_id(),
            name="Nexus Исполнитель",
            description="Исполнительская панель и связанные разделы.",
            is_system=False,
            read_assigned_sections=["executor", "tasks", "task_chat", "global_chat", "files_catalog", "mail", "work_results_reviews"],
        )
        state.roles["customer"] = customer_role

        users_seed = [
            ("admin", "admin@nexus-demo.ru", "Nexus Admin", state.roles["admin"].id),
            ("manager", "manager@nexus-demo.ru", "Анна Кузнецова", state.roles["manager"].id),
            ("finance", "finance@nexus-demo.ru", "Марина Лебедева", state.roles["finance"].id),
            ("contracts", "contracts@nexus-demo.ru", "Илья Романов", state.roles["contracts"].id),
            ("geo_lead", "geo.lead@testgeo-demo.ru", "Егор Серов", state.roles["executor"].id),
            ("fire_lead", "fire.lead@testfire-demo.ru", "Инна Пожарская", state.roles["executor"].id),
            ("hvac_lead", "hvac.lead@delta-demo.ru", "Дмитрий Климатов", state.roles["executor"].id),
            ("customer_aurora", "customer@aurora-demo.ru", "Ольга Заказчик", state.roles["customer"].id),
            ("customer_vector", "customer@vector-demo.ru", "Михаил Заказчик", state.roles["customer"].id),
        ]
        for key, email, full_name, role_id in users_seed:
            state.users[key] = User(
                id=_string_id(),
                email=email,
                full_name=full_name,
                password_hash=hash_password("Nexus123!"),
                role_id=role_id,
                is_active=True,
                rating=4.8,
                rating_count=12,
            )
            db.add(state.users[key])

        company_specs = [
            ("nexus_alpha", "7700100010", "internal", "Nexus Alpha", "Nexus Alpha", "ООО «Nexus Alpha»", "Мария Альфа", "+7 (495) 000-10-10", "alpha@nexus-demo.ru", "Москва, Тестовый проезд, 10"),
            ("nexus_beta", "7700200020", "internal", "Nexus Beta", "Nexus Beta", "ООО «Nexus Beta»", "Борис Бета", "+7 (495) 000-20-20", "beta@nexus-demo.ru", "Москва, Тестовый проезд, 20"),
            ("nexus_solo", "7700300030", "internal", "Nexus Solo", "Nexus Solo", "ИП Nexus Solo", "Никита Solo", "+7 (495) 000-30-30", "solo@nexus-demo.ru", "Москва, Тестовый проезд, 30"),
            ("aurora", "7701100110", "customer", "Aurora Development", "Aurora Development", "ООО «Aurora Development»", "Ольга Заказчик", "+7 (495) 100-10-10", "customer@aurora-demo.ru", "Санкт-Петербург, ул. Северная, 8"),
            ("vector", "7702200220", "customer", "Vector Energy", "Vector Energy", "АО «Vector Energy»", "Михаил Заказчик", "+7 (495) 200-20-20", "customer@vector-demo.ru", "Казань, пр-т Энергетиков, 14"),
            ("polar", "7703300330", "customer", "Polar Logistics", "Polar Logistics", "ООО «Polar Logistics»", "Ирина Полярная", "+7 (495) 300-30-30", "customer@polar-demo.ru", "Мурманск, портовая зона"),
            ("testgeo", "7704400440", "subcontractor", "TestGeo Partners", "TestGeo Partners", "ООО «TestGeo Partners»", "Егор Серов", "+7 (495) 400-40-40", "geo@testgeo-demo.ru", "Москва, Геодезическая, 4"),
            ("fireline", "7705500550", "subcontractor", "Fireline Systems", "Fireline Systems", "ООО «Fireline Systems»", "Инна Пожарская", "+7 (495) 500-50-50", "fire@testfire-demo.ru", "Нижний Новгород, Пожарная, 5"),
            ("delta_hvac", "7706600660", "subcontractor", "Delta HVAC", "Delta HVAC", "ООО «Delta HVAC»", "Дмитрий Климатов", "+7 (495) 600-60-60", "hvac@delta-demo.ru", "Екатеринбург, Климатическая, 6"),
            ("blue_ledger", "7707700770", "service", "Blue Ledger", "Blue Ledger", "ООО «Blue Ledger»", "Марина Лебедева", "+7 (495) 700-70-70", "finance@ledger-demo.ru", "Москва, Финансовая, 7"),
            ("legal_sandbox", "7708800880", "service", "Legal Sandbox", "Legal Sandbox", "ООО «Legal Sandbox»", "Илья Романов", "+7 (495) 800-80-80", "legal@sandbox-demo.ru", "Москва, Правовая, 8"),
        ]
        for key, inn, company_type, name, short_name, full_name, contact_person, phone, email, address in company_specs:
            company = Company(
                id=_string_id(),
                inn=inn,
                type=company_type,
                name=name,
                short_name=short_name,
                full_name=full_name,
                contact_person=contact_person,
                phone=phone,
                email=email,
                phones=[phone],
                emails=[email],
                bank_accounts=[
                    {
                        "bank_name": "Тест Банк",
                        "account": f"40702{inn[:10]}",
                        "bik": "044525000",
                        "corr_account": f"30101{inn[:10]}",
                    }
                ],
                address=address,
            )
            state.companies[key] = company
            db.add(company)

        company_links = [
            ("nexus_alpha", "manager", "leader"),
            ("nexus_beta", "contracts", "leader"),
            ("nexus_alpha", "finance", "employee"),
            ("nexus_alpha", "admin", "employee"),
            ("testgeo", "geo_lead", "leader"),
            ("fireline", "fire_lead", "leader"),
            ("delta_hvac", "hvac_lead", "leader"),
            ("aurora", "customer_aurora", "leader"),
            ("vector", "customer_vector", "leader"),
        ]
        for company_key, user_key, link_type in company_links:
            db.add(
                CompanyUserLink(
                    id=_string_id(),
                    company_id=state.companies[company_key].id,
                    user_id=state.users[user_key].id,
                    link_type=link_type,
                )
            )

        category_specs = [
            ("design", "Проектирование"),
            ("engineering", "Инженерные разделы"),
            ("expertise", "Экспертиза"),
            ("delivery", "Сопровождение"),
        ]
        for key, name in category_specs:
            state.product_categories[key] = ProductCategory(id=_uuid_id(), name=name)
            db.add(state.product_categories[key])

        product_specs = [
            ("survey", "Инженерные изыскания", "design", 180000.0),
            ("pd", "Проектная документация", "design", 950000.0),
            ("rd", "Рабочая документация", "design", 1350000.0),
            ("masterplan", "Генеральный план", "engineering", 420000.0),
            ("power", "Система электроснабжения", "engineering", 390000.0),
            ("fire", "Пожарная безопасность", "engineering", 330000.0),
            ("scs", "Сети связи", "engineering", 250000.0),
            ("estimate", "Сметная документация", "expertise", 110000.0),
            ("expertise", "Сопровождение экспертизы", "expertise", 210000.0),
            ("author", "Авторский надзор", "delivery", 95000.0),
        ]
        for key, name, category_key, base_price in product_specs:
            state.products[key] = Product(
                id=_uuid_id(),
                category_id=state.product_categories[category_key].id,
                name=name,
                base_price=base_price,
            )
            db.add(state.products[key])

        lead_specs = [
            ("aurora", "Aurora Campus | входящая заявка", "Aurora Campus Phase 1", "Санкт-Петербург, Северная площадка, участок 1", "nexus_alpha", "manager", "incoming", 2850000.0),
            ("vector", "Vector Edge Hub | входящая заявка", "Vector Edge Hub", "Казань, индустриальный парк Вектор", "nexus_beta", "contracts", "qualification", 3640000.0),
        ]
        for key, title, obj_name, address, our_company_key, user_key, status, total_value in lead_specs:
            lead = Lead(
                id=_string_id(),
                title=title,
                obj_name=obj_name,
                address=address,
                customer_id=state.companies[key].id,
                our_company_id=state.companies[our_company_key].id,
                responsible_user_id=state.users[user_key].id,
                status=status,
                total_value=total_value,
                advance_percent=20.0,
                vat_rate=20.0,
            )
            state.leads[key] = lead
            db.add(lead)

        deal_specs = [
            ("aurora", "Aurora Campus Phase 1", "Aurora Campus Phase 1", "Санкт-Петербург, Северная площадка, участок 1", "aurora", "nexus_alpha", "active", 4980000.0, 1480000.0),
            ("vector", "Vector Edge Hub", "Vector Edge Hub", "Казань, индустриальный парк Вектор", "vector", "nexus_beta", "active", 6120000.0, 2100000.0),
            ("polar", "Polar Logistics Terminal", "Polar Logistics Terminal", "Мурманск, портовая зона, терминал 4", "polar", "nexus_solo", "active", 2750000.0, 450000.0),
        ]
        for key, title, obj_name, address, customer_key, our_company_key, status, total_contract_value, total_paid in deal_specs:
            deal = Deal(
                id=_string_id(),
                title=title,
                obj_name=obj_name,
                address=address,
                customer_id=state.companies[customer_key].id,
                general_contractor_id=None,
                our_company_id=state.companies[our_company_key].id,
                status=status,
                total_contract_value=total_contract_value,
                total_paid=total_paid,
                vat_rate=20.0,
                vat_included=True,
            )
            state.deals[key] = deal
            db.add(deal)
            if key == "aurora":
                state.leads["aurora"].deal_id = deal.id
            if key == "vector":
                state.leads["vector"].deal_id = deal.id

        db.flush()

        for deal_key, user_key in [
            ("aurora", "manager"),
            ("vector", "manager"),
            ("vector", "contracts"),
            ("polar", "manager"),
        ]:
            db.add(DealGip(id=_string_id(), deal_id=state.deals[deal_key].id, user_id=state.users[user_key].id))

        stage_specs = [
            ("aurora_discovery", "aurora", "Старт и сбор исходных данных", date(2026, 4, 1), 12, "stage", "work_days", "completed"),
            ("aurora_pd", "aurora", "Проектная документация", date(2026, 4, 17), 24, "stage", "work_days", "in_progress"),
            ("aurora_rd", "aurora", "Рабочая документация", date(2026, 5, 20), 32, "stage", "work_days", "planned"),
            ("aurora_payment", "aurora", "Авансовый платеж", date(2026, 4, 5), 1, "payment", "calendar_days", "completed"),
            ("vector_plan", "vector", "Подготовка технического задания", date(2026, 4, 3), 10, "stage", "work_days", "completed"),
            ("vector_eng", "vector", "Разработка инженерных разделов", date(2026, 4, 18), 28, "stage", "work_days", "in_progress"),
            ("vector_exp", "vector", "Сопровождение экспертизы", date(2026, 5, 30), 18, "stage", "calendar_days", "planned"),
            ("polar_survey", "polar", "Изыскания и площадка", date(2026, 4, 7), 14, "stage", "work_days", "in_progress"),
            ("polar_design", "polar", "Разработка генплана", date(2026, 4, 28), 21, "stage", "work_days", "planned"),
            ("polar_author", "polar", "Авторский надзор", date(2026, 6, 1), 45, "other", "calendar_days", "planned"),
        ]
        for key, deal_key, name, date_start, duration, stage_type, term_type, status in stage_specs:
            stage = Stage(
                id=_uuid_id(),
                deal_id=_uuid_string(state.deals[deal_key].id),
                name=name,
                stage_type=stage_type,
                term_type=term_type,
                date_start=date_start,
                duration=duration,
                date_end=date_start + timedelta(days=duration),
                status=status,
                is_closed=status == "completed",
                planned_cost=0.0,
                actual_cost=0.0,
            )
            state.stages[key] = stage
            db.add(stage)

        dependency_specs = [
            ("aurora_discovery", "aurora_pd", "finish_to_start", 0),
            ("aurora_pd", "aurora_rd", "finish_to_start", 0),
            ("vector_plan", "vector_eng", "finish_to_start", 0),
            ("vector_eng", "vector_exp", "finish_to_start", 2),
            ("polar_survey", "polar_design", "finish_to_start", 0),
            ("polar_design", "polar_author", "finish_to_start", 5),
        ]
        for predecessor_key, successor_key, dependency_type, lag in dependency_specs:
            db.add(
                StageDependency(
                    id=_uuid_id(),
                    predecessor_id=state.stages[predecessor_key].id,
                    successor_id=state.stages[successor_key].id,
                    dependency_type=dependency_type,
                    lag=lag,
                )
            )

        deal_product_specs = [
            ("aurora_pd", "aurora", "pd", "Комплект ПД по корпусу A", 1, 780000.0, 20.0, "planned", "aurora_pd"),
            ("aurora_fire", "aurora", "fire", "Пожарная безопасность корпуса A", 1, 330000.0, 20.0, "in_progress", "aurora_pd"),
            ("aurora_scs", "aurora", "scs", "Сети связи корпуса A", 1, 250000.0, 20.0, "planned", "aurora_pd"),
            ("aurora_rd", "aurora", "rd", "Комплект РД по корпусу A", 1, 1240000.0, 20.0, "planned", "aurora_rd"),
            ("vector_rd", "vector", "rd", "РД инженерного узла", 1, 1380000.0, 20.0, "in_progress", "vector_eng"),
            ("vector_power", "vector", "power", "Электроснабжение и ИТП", 1, 390000.0, 20.0, "in_progress", "vector_eng"),
            ("vector_expertise", "vector", "expertise", "Сопровождение экспертизы", 1, 210000.0, 20.0, "planned", "vector_exp"),
            ("polar_survey", "polar", "survey", "Инженерные изыскания терминала", 1, 180000.0, 20.0, "in_progress", "polar_survey"),
            ("polar_masterplan", "polar", "masterplan", "Генплан терминала", 1, 420000.0, 20.0, "planned", "polar_design"),
            ("polar_author", "polar", "author", "Авторский надзор терминала", 1, 95000.0, 20.0, "planned", "polar_author"),
        ]
        for key, deal_key, product_key, custom_name, quantity, unit_price, tax_rate, status, stage_key in deal_product_specs:
            fields = money_fields(quantity, unit_price, tax_rate)
            item = DealProduct(
                id=_string_id(),
                deal_id=state.deals[deal_key].id,
                product_id=state.products[product_key].id.hex,
                custom_name=custom_name,
                quantity=fields["quantity"],
                unit="компл.",
                unit_price=fields["unit_price"],
                discount_percent=fields["discount_percent"],
                discount_amount=fields["discount_amount"],
                tax_rate=fields["tax_rate"],
                total_price=fields["total_price"],
                discount_total=fields["discount_total"],
                tax_amount=fields["tax_amount"],
                final_price=fields["final_price"],
                stage_id=state.stages[stage_key].id.hex,
                status=status,
            )
            state.deal_products[key] = item
            db.add(item)

        lead_product_specs = [
            ("lead_aurora_pd", "aurora", "pd", "Предварительная оценка ПД", 1, 720000.0),
            ("lead_aurora_fire", "aurora", "fire", "Предварительная оценка СПБ", 1, 280000.0),
            ("lead_vector_rd", "vector", "rd", "Предварительная оценка РД", 1, 1260000.0),
        ]
        for key, lead_key, product_key, custom_name, quantity, unit_price in lead_product_specs:
            fields = money_fields(quantity, unit_price, 20.0)
            db.add(
                LeadProduct(
                    id=_string_id(),
                    lead_id=state.leads[lead_key].id,
                    product_id=state.products[product_key].id.hex,
                    custom_name=custom_name,
                    quantity=fields["quantity"],
                    unit="компл.",
                    unit_price=fields["unit_price"],
                    discount_percent=fields["discount_percent"],
                    discount_amount=fields["discount_amount"],
                    tax_rate=fields["tax_rate"],
                    total_price=fields["total_price"],
                    discount_total=fields["discount_total"],
                    tax_amount=fields["tax_amount"],
                    final_price=fields["final_price"],
                )
            )

        for product_key, item in state.deal_products.items():
            db.add(
                StageProductLink(
                    id=_string_id(),
                    deal_id=item.deal_id,
                    stage_id=item.stage_id,
                    deal_product_id=item.id,
                )
            )

        contract_specs = [
            ("aurora_main", "AUR-2026-01", date(2026, 4, 2), "general_contractor", "completed", 4980000.0, "aurora", "nexus_alpha", "aurora", None),
            ("vector_main", "VEC-2026-07", date(2026, 4, 6), "services", "in_progress", 6120000.0, "vector", "nexus_beta", "vector", None),
            ("geo_sub", "SUB-GEO-01", date(2026, 4, 10), "subcontractor", "completed", 420000.0, "nexus_alpha", "testgeo", "aurora", None),
            ("fire_sub", "SUB-FIRE-01", date(2026, 4, 11), "subcontractor", "in_progress", 330000.0, "nexus_alpha", "fireline", "aurora", None),
            ("hvac_sub", "SUB-HVAC-01", date(2026, 4, 12), "subcontractor", "in_progress", 390000.0, "nexus_beta", "delta_hvac", "vector", None),
        ]
        for key, number, contract_date, contract_type, status, amount, customer_key, executor_key, deal_key, card_key in contract_specs:
            contract = Contract(
                id=_uuid_id(),
                contract_number=number,
                contract_date=contract_date,
                contract_type=contract_type,
                status=status,
                amount=amount,
                customer_id=_uuid_string(state.companies[customer_key].id),
                executor_id=_uuid_string(state.companies[executor_key].id),
                deal_id=_uuid_string(state.deals[deal_key].id),
                subcontractor_card_id=_uuid_string(state.subcontractor_cards[card_key].id) if card_key else None,
            )
            state.contracts[key] = contract
            db.add(contract)

        subcontractor_card_specs = [
            ("aurora_geo", "Aurora | Геодезия", "Aurora Campus Phase 1", "Санкт-Петербург, Северная площадка, участок 1", "testgeo", "aurora", "nexus_alpha", 420000.0),
            ("aurora_fire", "Aurora | Пожарная безопасность", "Aurora Campus Phase 1", "Санкт-Петербург, Северная площадка, участок 1", "fireline", "aurora", "nexus_alpha", 330000.0),
            ("vector_hvac", "Vector | HVAC", "Vector Edge Hub", "Казань, индустриальный парк Вектор", "delta_hvac", "vector", "nexus_beta", 390000.0),
        ]
        for key, title, obj_name, address, company_key, customer_key, gc_key, value in subcontractor_card_specs:
            card = SubcontractorCard(
                id=_string_id(),
                title=title,
                obj_name=obj_name,
                address=address,
                company_id=state.companies[company_key].id,
                customer_id=state.companies[customer_key].id,
                general_contractor_id=state.companies[gc_key].id,
                status="active",
                total_contract_value=value,
                total_paid=value * 0.35,
                vat_rate=20.0,
                vat_included=True,
            )
            state.subcontractor_cards[key] = card
            db.add(card)

        db.flush()

        card_to_contract = {
            "aurora_geo": "geo_sub",
            "aurora_fire": "fire_sub",
            "vector_hvac": "hvac_sub",
        }
        for card_key, contract_key in card_to_contract.items():
            state.contracts[contract_key].subcontractor_card_id = state.subcontractor_cards[card_key].id

        subcontractor_stage_specs = [
            ("geo_stage", "aurora_geo", "testgeo", "Геодезическая подоснова", date(2026, 4, 12), 12, "geo_sub", "completed"),
            ("fire_stage", "aurora_fire", "fireline", "Раздел СПС и СОУЭ", date(2026, 4, 20), 18, "fire_sub", "in_progress"),
            ("hvac_stage", "vector_hvac", "delta_hvac", "Раздел ОВК и ИТП", date(2026, 4, 22), 21, "hvac_sub", "in_progress"),
        ]
        for key, card_key, company_key, name, date_start, duration, contract_key, status in subcontractor_stage_specs:
            stage = SubcontractorStage(
                id=_uuid_id(),
                subcontractor_card_id=state.subcontractor_cards[card_key].id,
                contract_id=state.contracts[contract_key].id.hex,
                name=name,
                date_start=date_start,
                duration=duration,
                date_end=date_start + timedelta(days=duration),
                status=status,
                stage_type="stage",
                term_type="work_days",
                planned_cost=0.0,
                actual_cost=0.0,
                subcontractor_id=_uuid_string(state.companies[company_key].id),
            )
            state.subcontractor_stages[key] = stage
            db.add(stage)

        subcontractor_product_specs = [
            ("geo_product", "aurora_geo", "masterplan", "Геоподоснова и планировочные ограничения", 1, 420000.0, "geo_stage", "geo_sub"),
            ("fire_product", "aurora_fire", "fire", "Раздел СПС и СОУЭ", 1, 330000.0, "fire_stage", "fire_sub"),
            ("hvac_product", "vector_hvac", "power", "Раздел ОВК и ИТП", 1, 390000.0, "hvac_stage", "hvac_sub"),
        ]
        for key, card_key, product_key, custom_name, quantity, unit_price, stage_key, contract_key in subcontractor_product_specs:
            fields = money_fields(quantity, unit_price, 20.0)
            product = SubcontractorProduct(
                id=_string_id(),
                subcontractor_card_id=state.subcontractor_cards[card_key].id,
                product_id=state.products[product_key].id.hex,
                contract_id=state.contracts[contract_key].id.hex,
                stage_id=state.subcontractor_stages[stage_key].id.hex,
                custom_name=custom_name,
                quantity=fields["quantity"],
                unit="компл.",
                unit_price=fields["unit_price"],
                discount_percent=fields["discount_percent"],
                discount_amount=fields["discount_amount"],
                tax_rate=fields["tax_rate"],
                total_price=fields["total_price"],
                discount_total=fields["discount_total"],
                tax_amount=fields["tax_amount"],
                final_price=fields["final_price"],
                status="in_progress",
            )
            state.subcontractor_products[key] = product
            db.add(product)

        assignment_specs = [
            ("aurora_masterplan", "aurora", "aurora_pd", "masterplan", "aurora_geo", "geo_product", "geo_sub", date(2026, 4, 17), date(2026, 4, 29), date(2026, 5, 4), "in_progress"),
            ("aurora_fire", "aurora", "aurora_pd", "fire", "aurora_fire", "fire_product", "fire_sub", date(2026, 4, 20), date(2026, 5, 12), date(2026, 5, 15), "in_progress"),
            ("vector_power", "vector", "vector_eng", "power", "vector_hvac", "hvac_product", "hvac_sub", date(2026, 4, 22), date(2026, 5, 20), date(2026, 5, 24), "not_started"),
        ]
        for key, deal_key, stage_key, product_key, card_key, subcontractor_product_key, contract_key, start_date, due_date, contract_due_date, status in assignment_specs:
            assignment = StageProductAssignment(
                id=_string_id(),
                deal_id=state.deals[deal_key].id,
                stage_id=state.stages[stage_key].id.hex,
                product_id=state.products[product_key].id.hex,
                subcontractor_card_id=state.subcontractor_cards[card_key].id,
                subcontractor_product_id=state.subcontractor_products[subcontractor_product_key].id,
                contract_id=state.contracts[contract_key].id.hex,
                start_date=start_date,
                due_date=due_date,
                contract_due_date=contract_due_date,
                status=status,
            )
            state.assignments[key] = assignment
            db.add(assignment)
            for subtask_index, suffix in enumerate(("Подготовка", "Выпуск"), start=1):
                db.add(
                    StageProductSubtask(
                        id=_string_id(),
                        assignment_id=assignment.id,
                        title=f"{state.products[product_key].name} {suffix}",
                        due_date=start_date + timedelta(days=subtask_index * 5),
                        status="completed" if subtask_index == 1 and status == "in_progress" else "in_progress",
                    )
                )

        task_specs = [
            ("survey_approval", "Согласовать комплект изысканий", "Проверить комплект геодезии и исходных данных.", "aurora", "aurora_pd", "manager", "contracts", "in_progress", date(2026, 4, 18), date(2026, 4, 24), 55000.0),
            ("fire_review", "Проверить раздел СПС", "Сверить состав оборудования и замечания заказчика.", "aurora", "aurora_pd", "contracts", "manager", "pending", date(2026, 4, 21), date(2026, 5, 2), 38000.0),
            ("vector_letter", "Подготовить письмо в экспертизу", "Подготовить сопроводительное письмо и комплект приложений.", "vector", "vector_exp", "contracts", "manager", "in_progress", date(2026, 5, 30), date(2026, 6, 3), 22000.0),
        ]
        for key, title, description, deal_key, stage_key, assignee_key, creator_key, status, start_date, due_date, budget in task_specs:
            task = Task(
                id=_string_id(),
                deal_id=state.deals[deal_key].id,
                stage_id=state.stages[stage_key].id.hex,
                title=title,
                description=description,
                status=status,
                priority="normal",
                assigned_to_user_id=state.users[assignee_key].id,
                created_by_user_id=state.users[creator_key].id,
                start_date=start_date,
                due_date=due_date,
                budget=budget,
                attachments=[],
                tags=["testportal", deal_key],
            )
            state.tasks[key] = task
            db.add(task)

        db.flush()

        task_attachment_path = write_docx("/tasks/attachments/checklist.docx", "Nexus Checklist", "Тестовый чек-лист задачи.")
        for task in state.tasks.values():
            task.attachments = [
                {
                    "name": "checklist.docx",
                    "storage_path": task_attachment_path,
                    "size": len(task_attachment_path),
                }
            ]

        task_message_specs = [
            ("survey_approval", "manager", "Проверьте комплект до пятницы."),
            ("survey_approval", "contracts", "Взял в работу, замечания внесу вечером."),
            ("fire_review", "contracts", "Нужно уточнить марку оборудования."),
            ("vector_letter", "manager", "Письмо и приложения должны уйти одним пакетом."),
        ]
        for task_key, user_key, body in task_message_specs:
            db.add(TaskMessage(id=_string_id(), task_id=state.tasks[task_key].id, user_id=state.users[user_key].id, body=body, attachments=[], mentions=[]))

        conversation = ChatConversation(
            id=_string_id(),
            type="global",
            title="Nexus HQ",
            description="Тестовый корпоративный чат",
            created_by_user_id=state.users["admin"].id,
        )
        db.add(conversation)
        for user_key, role in [("admin", "owner"), ("manager", "member"), ("finance", "member"), ("contracts", "member"), ("geo_lead", "member")]:
            db.add(ChatConversationMember(id=_string_id(), conversation_id=conversation.id, user_id=state.users[user_key].id, role=role))
        for user_key, body in [
            ("admin", "Добро пожаловать в тестовый портал Nexus."),
            ("manager", "По Aurora и Vector все тестовые данные загружены."),
            ("finance", "Казначейство и ДДС тоже заполнены тестом."),
        ]:
            db.add(GlobalChatMessage(id=_string_id(), conversation_id=conversation.id, user_id=state.users[user_key].id, body=body, attachments=[], mentions=[]))

        auction = TaskAuction(
            id=_string_id(),
            title="Аукцион на раздел СПС",
            description="Тестовый подбор исполнителя по разделу СПС.",
            budget=330000.0,
            deal_id=state.deals["aurora"].id,
            category_code="5.5.3",
            allow_custom_price=True,
            status="awarded",
            winner_id=state.users["fire_lead"].id,
            created_by_id=state.users["manager"].id,
            created_task_id=state.tasks["fire_review"].id,
        )
        db.add(auction)
        db.flush()
        bid_a = TaskAuctionBid(id=_string_id(), auction_id=auction.id, user_id=state.users["fire_lead"].id, bid_price=325000.0, covers_children=True, comment="Готовы взять в работу.")
        bid_b = TaskAuctionBid(id=_string_id(), auction_id=auction.id, user_id=state.users["geo_lead"].id, bid_price=340000.0, covers_children=False, comment="Можем подключить смежников.")
        auction.winner_bid_id = bid_a.id
        db.add_all([bid_a, bid_b])

        for key, rate_date, rate_value in [
            ("cb_apr", date(2026, 4, 1), 14.5),
            ("cb_may", date(2026, 5, 1), 14.0),
            ("cb_jun", date(2026, 6, 1), 13.75),
        ]:
            db.add(CBRate(id=_uuid_id(), rate_date=rate_date, rate_value=rate_value))

        financial_plans: Dict[str, FinancialPlan] = {}
        financial_plan_specs = [
            ("aurora_income", "aurora", "income", 1480000.0, date(2026, 4, 5), date(2026, 4, 5), "Аванс заказчика", "aurora", None, "paid", "aurora_payment"),
            ("aurora_fire_expense", "aurora", "expense", 330000.0, date(2026, 5, 15), date(2026, 5, 20), "Оплата Fireline", "fireline", "SUB-FIRE-01", "partial", "aurora_pd"),
            ("vector_income", "vector", "income", 2100000.0, date(2026, 4, 18), date(2026, 4, 18), "Платеж Vector", "vector", None, "partial", "vector_plan"),
            ("polar_expense", "polar", "expense", 180000.0, date(2026, 4, 22), date(2026, 4, 25), "Изыскания площадки", "testgeo", "SUB-GEO-01", "unpaid", "polar_survey"),
        ]
        for key, deal_key, direction, amount_plan, date_plan_start, date_plan_end, description, company_key, subcontractor_contract_id, payment_status, stage_key in financial_plan_specs:
            plan = FinancialPlan(
                id=_uuid_id(),
                deal_id=_uuid_string(state.deals[deal_key].id),
                direction=direction,
                amount_plan=amount_plan,
                date_plan_start=date_plan_start,
                date_plan_end=date_plan_end,
                description=description,
                contractor_id=_uuid_string(state.companies[company_key].id),
                subcontractor_contract_id=subcontractor_contract_id,
                payment_status=payment_status,
                stage_id=state.stages[stage_key].id,
            )
            financial_plans[key] = plan
            db.add(plan)

        entries: Dict[str, IncomeExpenseEntry] = {}
        entry_specs = [
            ("aurora_income", "income", 1480000.0, date(2026, 4, 5), date(2026, 4, 5), "aurora", "nexus_alpha", "aurora", "aurora_main", "aurora_payment", "1.1"),
            ("aurora_fire_expense", "expense", 330000.0, date(2026, 5, 15), None, "nexus_alpha", "fireline", "aurora", "fire_sub", "aurora_pd", "5.5.3"),
            ("vector_income", "income", 2100000.0, date(2026, 4, 18), date(2026, 4, 18), "vector", "nexus_beta", "vector", "vector_main", "vector_plan", "1.2"),
            ("polar_expense", "expense", 180000.0, date(2026, 4, 22), None, "nexus_solo", "testgeo", "polar", "geo_sub", "polar_survey", "2.1"),
        ]
        for key, direction, amount, plan_date, actual_date, payer_key, payee_key, deal_key, contract_key, stage_key, category_code in entry_specs:
            entry = IncomeExpenseEntry(
                id=_string_id(),
                direction=direction,
                amount=amount,
                plan_date=plan_date,
                actual_date=actual_date,
                payer_id=state.companies[payer_key].id,
                payee_id=state.companies[payee_key].id,
                deal_id=state.deals[deal_key].id,
                contract_id=state.contracts[contract_key].id.hex,
                stage_id=state.stages[stage_key].id.hex,
                category_code=category_code,
            )
            entries[key] = entry
            db.add(entry)

        transactions: Dict[str, TreasuryTransaction] = {}
        transaction_specs = [
            ("tx_aurora", "TRX-1001", date(2026, 4, 5), 1480000.0, "Aurora Development", "Nexus Alpha", "Аванс по договору AUR-2026-01", "1.1", "Да", "processed"),
            ("tx_vector", "TRX-1002", date(2026, 4, 18), 2100000.0, "Vector Energy", "Nexus Beta", "Оплата по договору VEC-2026-07", "1.2", "Нет", "processed"),
            ("tx_fire", "TRX-1003", date(2026, 5, 20), 198000.0, "Nexus Alpha", "Fireline Systems", "Частичная оплата SUB-FIRE-01", "5.5.3", "Нет", "pending"),
        ]
        for key, doc_num, tx_date, amount, payer_name, payee_name, purpose, category_code, ignore_flag, processed in transaction_specs:
            tx = TreasuryTransaction(
                id=_uuid_id(),
                doc_num=doc_num,
                transaction_date=tx_date,
                amount=amount,
                payer_name=payer_name,
                payee_name=payee_name,
                payer_inn="7700000000",
                payee_inn="7711111111",
                purpose=purpose,
                category_code=category_code,
                income_expense_id=entries["aurora_income"].id if key == "tx_aurora" else entries["vector_income"].id if key == "tx_vector" else entries["aurora_fire_expense"].id,
                ignore_flag=ignore_flag,
                auto_rule_id=None,
                remainder=0.0 if key != "tx_fire" else 132000.0,
                processed=processed,
            )
            transactions[key] = tx
            db.add(tx)

        db.flush()

        db.add(TreasuryAllocation(id=_uuid_id(), transaction_id=transactions["tx_aurora"].id, income_expense_id=entries["aurora_income"].id, amount=1480000.0, category_code="1.1"))
        db.add(TreasuryAllocation(id=_uuid_id(), transaction_id=transactions["tx_fire"].id, income_expense_id=entries["aurora_fire_expense"].id, amount=198000.0, category_code="5.5.3"))
        db.add(TransactionAllocation(id=_uuid_id(), transaction_id=transactions["tx_aurora"].id, financial_plan_id=financial_plans["aurora_income"].id, amount=1480000.0))
        db.add(TreasuryAutoRule(id=_string_id(), name="Nexus income", match_text="AUR-2026-01", match_type="contains", action_type="create_dds", category_code="1.1", create_dds=True, is_active=True, priority=10))
        db.add(TreasuryAutoRule(id=_string_id(), name="Fire expense", match_text="SUB-FIRE-01", match_type="contains", action_type="create_dds", category_code="5.5.3", create_dds=True, is_active=True, priority=20))
        db.add(TreasuryAutoRule(id=_string_id(), name="Ignore bank fee", match_text="Комиссия банка", match_type="contains", action_type="ignore", category_code=None, create_dds=False, is_active=True, priority=30))

        for contract_key, title in [("aurora_main", "Основной договор Aurora"), ("vector_main", "Основной договор Vector"), ("geo_sub", "Субдоговор геодезии"), ("fire_sub", "Субдоговор пожарной безопасности"), ("hvac_sub", "Субдоговор HVAC")]:
            contract = state.contracts[contract_key]
            contract_dir = f"/contracts/{contract.id.hex}"
            pdf_path = write_pdf(f"{contract_dir}/main.pdf", title, f"Номер: {contract.contract_number}", "Тестовый договор Nexus.")
            docx_path = write_docx(f"{contract_dir}/main.docx", title, f"Номер: {contract.contract_number}", "Тестовая редакция договора.")
            doc_status = "signed" if contract.status == "completed" else "draft"
            db.add(ContractDocument(id=_uuid_id(), contract_id=contract.id, doc_type="contract", number_in_contract=1, status=doc_status, pdf_file_name=f"{contract.contract_number}.pdf", pdf_storage_path=pdf_path, edit_file_name=f"{contract.contract_number}.docx", edit_storage_path=docx_path))
            if contract_key in {"aurora_main", "vector_main"}:
                appendix_path = write_pdf(f"{contract_dir}/appendix_1.pdf", f"Приложение к {contract.contract_number}", "Тестовое приложение 1")
                db.add(ContractDocument(id=_uuid_id(), contract_id=contract.id, doc_type="appendix", number_in_contract=1, status="signed", pdf_file_name=f"{contract.contract_number}-appendix.pdf", pdf_storage_path=appendix_path))

        for key, result_title, stage_key, card_key, deal_key, reviewer_key, creator_name in [
            ("geo_result", "Геоподоснова", "geo_stage", "aurora_geo", "aurora", "manager", "Егор Серов"),
            ("fire_result", "СПС и СОУЭ", "fire_stage", "aurora_fire", "aurora", "contracts", "Инна Пожарская"),
            ("hvac_result", "ОВК и ИТП", "hvac_stage", "vector_hvac", "vector", "manager", "Дмитрий Климатов"),
        ]:
            storage_path = write_pdf(f"/results/{key}.pdf", result_title, "Тестовый результат работ.")
            db.add(StageResult(id=_string_id(), stage_id=str(state.subcontractor_stages[stage_key].id), subcontractor_card_id=state.subcontractor_cards[card_key].id, deal_id=state.deals[deal_key].id, product_name=result_title, version_label="v1", version_number=1, comment="Тестовый выпуск", reviewer_comment="Принято для демо", status="accepted" if key == "geo_result" else "review", reviewer_id=state.users[reviewer_key].id, reviewed_at=datetime.now(timezone.utc), storage_path=storage_path, public_url=storage_path, created_by=creator_name))
            db.add(WorkResult(id=_uuid_id(), stage_id=state.stages["aurora_pd" if deal_key == "aurora" else "vector_eng"].id, subcontractor_id=_uuid_string(state.companies["testgeo" if key == "geo_result" else "fireline" if key == "fire_result" else "delta_hvac"].id), version=1, status="accepted" if key == "geo_result" else "review", s3_object_key=storage_path, comment_sub="Передано на проверку", comment_gip="В работе"))

        for seq_key, seq_value in [("normbud", 600), ("bayer", 700), ("morozov", 800)]:
            db.add(OutgoingNumberSequence(our_company_key=seq_key, next_seq=seq_value))

        outgoing_specs = [
            ("aurora_letter", 600, "600/2026-04", "bayer", "aurora", "aurora", date(2026, 4, 16), "Передача комплекта ПД", "Уважаемые коллеги,\nнаправляем комплект проектной документации.", "Aurora Development"),
            ("vector_letter", 700, "700/2026-04", "normbud", "vector", "vector", date(2026, 4, 22), "Ответ на замечания", "Направляем ответы на замечания экспертизы.", "Vector Energy"),
            ("polar_letter", 800, "800/2026-04", "morozov", "polar", "polar", date(2026, 4, 28), "Передача генплана", "Передаем рабочий комплект генплана.", "Polar Logistics"),
        ]
        for key, seq, number, company_key, recipient_company_key, deal_key, letter_date, subject, body, recipient_short_name in outgoing_specs:
            doc = OutgoingDocument(id=_string_id(), outgoing_number_seq=seq, outgoing_number=number, our_company_key=company_key, outgoing_number_company_seq=seq, recipient_company_id=state.companies[recipient_company_key].id, deal_id=state.deals[deal_key].id, letter_date=letter_date, subject=subject, body=body, recipient_short_name=recipient_short_name, recipient_to_name="Руководителю проекта", recipient_appeal="Уважаемые коллеги!", recipient_eio="Тестов Тест Тестович", recipient_salutation="Уважаемый", status="sent")
            state.outgoing_documents[key] = doc
            db.add(doc)
        db.flush()
        for key, doc in state.outgoing_documents.items():
            base_dir = f"/outgoing/{doc.id}"
            pdf_path = write_pdf(f"{base_dir}/current.pdf", doc.subject, doc.body, f"Получатель: {doc.recipient_short_name}")
            docx_path = write_docx(f"{base_dir}/current.docx", doc.subject, doc.body, f"Получатель: {doc.recipient_short_name}")
            version = OutgoingDocumentVersion(id=_string_id(), document_id=doc.id, version_number=1, status="approved", created_by=state.users["contracts"].email, comment="Тестовая версия", pdf_path=pdf_path, pdf_public_url=pdf_path)
            db.add(version)
            db.flush()
            db.add(OutgoingDocumentFile(id=_string_id(), document_id=doc.id, version_id=version.id, file_type="pdf_current", file_path=pdf_path, file_name=f"{doc.outgoing_number}.pdf", public_url=pdf_path))
            db.add(OutgoingDocumentFile(id=_string_id(), document_id=doc.id, version_id=version.id, file_type="docx_current", file_path=docx_path, file_name=f"{doc.outgoing_number}.docx", public_url=docx_path))

        document_specs = [
            ("aurora_pkg_pd", "package", "Aurora | Комплект ПД", "PKG-001", date(2026, 4, 16), "sent", "aurora", "aurora", "nexus_alpha", "outgoing", state.outgoing_documents["aurora_letter"].id),
            ("vector_review", "letter", "Vector | Ответ на замечания", "LTR-001", date(2026, 4, 22), "signed", "vector", "vector", "nexus_beta", "outgoing", state.outgoing_documents["vector_letter"].id),
            ("polar_masterplan", "rd", "Polar | Генплан", "RD-001", date(2026, 4, 28), "draft", "polar", "polar", "nexus_solo", "outgoing", state.outgoing_documents["polar_letter"].id),
        ]
        for key, doc_type, title, number, document_date, status, project_key, counterparty_key, our_company_key, source_type, source_id in document_specs:
            doc = Document(id=_string_id(), doc_type=doc_type, title=title, number=number, document_date=document_date, status=status, project_id=state.deals[project_key].id, counterparty_id=state.companies[counterparty_key].id, our_company_id=state.companies[our_company_key].id, source_type=source_type, source_id=source_id)
            state.documents[key] = doc
            db.add(doc)
        db.flush()
        db.add(DocumentRelation(id=_string_id(), document_id=state.documents["aurora_pkg_pd"].id, related_document_id=state.documents["vector_review"].id, relation_type="reply"))
        package = DocumentPackage(id=_string_id(), title="Пакет Aurora №1", package_date=date(2026, 4, 16), status="sent", project_id=state.deals["aurora"].id, counterparty_id=state.companies["aurora"].id, our_company_id=state.companies["nexus_alpha"].id)
        db.add(package)
        db.flush()
        db.add(DocumentPackageItem(id=_string_id(), package_id=package.id, document_id=state.documents["aurora_pkg_pd"].id))
        dispatch = DocumentDispatch(id=_string_id(), package_id=package.id, status="delivered", note="Передано в демо-пакете")
        db.add(dispatch)
        db.flush()
        db.add(DocumentDispatchChannel(id=_string_id(), dispatch_id=dispatch.id, channel="email", channel_date=date(2026, 4, 16), confirmation_file="/document-registry/confirm-email.pdf", track_number="EMAIL-DEMO"))
        db.add(DocumentDispatchChannel(id=_string_id(), dispatch_id=dispatch.id, channel="courier", channel_date=date(2026, 4, 17), confirmation_file="/document-registry/confirm-courier.pdf", track_number="COURIER-DEMO"))

        kp_docx = write_docx("/kp/nexus-template.docx", "Nexus КП", "Тестовый шаблон коммерческого предложения")
        kp_pdf = write_pdf("/kp/nexus-template.pdf", "Nexus КП", "Тестовый шаблон")
        kp_template = KpTemplate(id=_string_id(), name="Nexus Standard", docx_url=kp_docx, pdf_url=kp_pdf, is_active=1)
        db.add(kp_template)
        db.flush()
        db.add(KpTemplateBinding(id=_string_id(), template_id=kp_template.id, our_company_id=state.companies["nexus_alpha"].id))
        kp_document = KpDocument(id=_string_id(), lead_id=state.leads["aurora"].id, number_seq=1, number_display="КП-001", status="sent", current_version=1, our_company_id=state.companies["nexus_alpha"].id, template_id=kp_template.id)
        db.add(kp_document)
        db.flush()
        db.add(KpVersion(id=_string_id(), kp_id=kp_document.id, version=1, docx_url=kp_docx, pdf_url=kp_pdf, total_amount=1180000.0, vat_amount=196666.67, total_text="Один миллион сто восемьдесят тысяч рублей", vat_text="НДС 20% включен", template_id=kp_template.id))

        mailbox_alpha = Mailbox(id=_string_id(), name="Nexus Alpha Mail", email="alpha@nexus-demo.ru", provider="yandex", status="connected", last_uid="104")
        mailbox_beta = Mailbox(id=_string_id(), name="Nexus Beta Mail", email="beta@nexus-demo.ru", provider="yandex", status="connected", last_uid="205")
        state.mailboxes["alpha"] = mailbox_alpha
        state.mailboxes["beta"] = mailbox_beta
        db.add_all([mailbox_alpha, mailbox_beta])
        db.flush()
        for mailbox_key, uid, subject, from_addr, snippet, has_attachments in [
            ("alpha", "101", "Aurora: комплект ПД", "customer@aurora-demo.ru", "Получили комплект, спасибо.", True),
            ("alpha", "102", "Aurora: замечания", "customer@aurora-demo.ru", "Просим уточнить раздел СПБ.", False),
            ("beta", "201", "Vector: письмо в экспертизу", "customer@vector-demo.ru", "Подтверждаем получение пакета.", True),
        ]:
            db.add(MailMessage(id=_string_id(), mailbox_id=state.mailboxes[mailbox_key].id, uid=uid, message_id=f"<{uid}@nexus-demo.ru>", subject=subject, from_addr=from_addr, to_addr=state.mailboxes[mailbox_key].email, date=datetime.now(timezone.utc), snippet=snippet, flags="\\Seen", has_attachments=has_attachments))

        notification_rule = NotificationRule(id=_string_id(), name="Просрочка этапа", is_active=True, trigger="stage_overdue", entity_type="stage", priority="warning", audience_type="assigned_user", require_subscription=False, conditions={"days_overdue": 1}, title_template="Этап просрочен", message_template="Этап {{name}} просрочен", action_url_template="/projects/{{deal_id}}?tab=stages", created_by=state.users["admin"].id)
        db.add(notification_rule)
        for user_key, title, message in [
            ("manager", "Aurora: нужен комплект ПД", "Проверьте готовность проектной документации."),
            ("finance", "Vector: ожидается платеж", "Ожидается поступление второго транша."),
            ("contracts", "Письмо заказчику готово", "Исходящее письмо по Vector можно отправлять."),
        ]:
            db.add(Notification(id=_string_id(), user_id=state.users[user_key].id, type="info", priority="info", title=title, message=message, entity_type="deal", entity_id=state.deals["aurora"].id if user_key == "manager" else state.deals["vector"].id, action_url="/projects", rule_id=notification_rule.id, source_event_id=_string_id(), is_read=False))
        for user_key in ("manager", "finance", "contracts"):
            db.add(NotificationPreference(user_id=state.users[user_key].id, timezone="Europe/Moscow", quiet_hours_start="22:00", quiet_hours_end="08:00", digest_enabled=True, digest_time="09:30", deliver_in_app=True))
        db.add(NotificationSubscription(id=_string_id(), user_id=state.users["manager"].id, entity_type="deal", entity_id=state.deals["aurora"].id, is_muted=False))
        db.add(NotificationJob(name="digest", last_run_at=datetime.now(timezone.utc) - timedelta(hours=3)))

        legal_case = LegalCase(id=_string_id(), case_number="А40-2026/001", judge="Смирнова И.А.", jurisdiction="Арбитражный суд города Москвы", judge_assistant="Иванова А.А.", judge_assistant_phone="+7 (495) 111-22-33", plaintiff_id=state.companies["nexus_alpha"].id, defendant_id=state.companies["polar"].id, description="Тестовое дело по просрочке предоставления исходных данных.")
        db.add(legal_case)
        db.flush()
        legal_event = LegalCaseEvent(id=_string_id(), legal_case_id=legal_case.id, event_type="Заседание", event_date=date(2026, 5, 14), event_time=time(11, 0), courtroom="Зал 5")
        db.add(legal_event)
        db.flush()
        legal_file_path = write_pdf("/legal/case-aurora-hearing.pdf", "Заседание", "Тестовое подтверждение заседания.")
        db.add(LegalCaseEventFile(id=_string_id(), event_id=legal_event.id, file_name="hearing.pdf", yandex_path=legal_file_path, storage_path=legal_file_path))
        db.add(LegalCaseTask(id=_string_id(), legal_case_id=legal_case.id, task_id=state.tasks["vector_letter"].id))

        for company_key, doc_type, file_name in [("testgeo", "portfolio", "testgeo-portfolio.pdf"), ("fireline", "license", "fireline-license.pdf"), ("delta_hvac", "sro", "delta-sro.pdf")]:
            storage_path = write_pdf(f"/companies/{company_key}/{file_name}", company_key, "Тестовый файл контрагента.")
            db.add(CompanyDocument(id=_string_id(), company_id=state.companies[company_key].id, doc_type=doc_type, file_name=file_name, file_url=storage_path, storage_path=storage_path, status="approved", comment="Тестовый документ"))
            db.add(CompanyAccreditation(id=_string_id(), company_id=state.companies[company_key].id, direction_id=str(state.product_categories["engineering"].id), status="approved", comment="Допущен в тестовом портале"))

        tender = Tender(id=_string_id(), deal_product_id=state.deal_products["vector_power"].id, deal_id=state.deals["vector"].id, product_id=state.products["power"].id.hex, direction_id=str(state.product_categories["engineering"].id), status="review", winner_company_id=state.companies["delta_hvac"].id)
        db.add(tender)
        db.flush()
        db.add(TenderOffer(id=_string_id(), tender_id=tender.id, company_id=state.companies["delta_hvac"].id, status="winner", proposed_amount=390000.0, proposed_deadline=date(2026, 5, 20), comment="Подтверждаем выполнение."))
        db.add(TenderOffer(id=_string_id(), tender_id=tender.id, company_id=state.companies["fireline"].id, status="responded", proposed_amount=410000.0, proposed_deadline=date(2026, 5, 23), comment="Готовы выполнить со смежниками."))

        db.add(PenaltyRule(id=_string_id(), rule_type="rating", condition_min=1, condition_max=2, coefficient=0.8, description="Низкий рейтинг", is_active=True, sort_order=1))
        db.add(PenaltyRule(id=_string_id(), rule_type="deadline", condition_min=10, condition_max=25, coefficient=0.9, description="Просрочка 10-25%", is_active=True, sort_order=2))
        db.add(UploadJob(id=_string_id(), status="completed", module="contracts", entity_id=str(state.contracts["aurora_main"].id), file_kind="pdf", file_name="AUR-2026-01.pdf", temp_path="/tmp/aur.pdf", target_path="/contracts/aurora/main.pdf", size_bytes=2048, created_by=state.users["contracts"].id, meta={"variant": "test_portal"}))
        db.add(AuditLog(id=_string_id(), entity_type="deal", entity_id=state.deals["aurora"].id, action="seed_created", user_id=state.users["admin"].id, source_event_id="seed-bootstrap", details="Тестовая сделка создана для локального портала."))
        db.add(EventLog(id=_string_id(), entity_type="portal", entity_id=None, action="bootstrap", details="Инициализирован тестовый портал Nexus", created_by="bootstrap_test_portal"))

        db.commit()

        return state
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def populate_storage_roots(state: SeedState) -> None:
    deal_storage_specs = [
        (
            "aurora",
            {
                "tz": [
                    ("01_Техническое задание.pdf", "Aurora | ТЗ", ["Тестовое техническое задание по гостиничному комплексу."]),
                    ("02_Исходные данные.docx", "Aurora | Исходные данные", ["ГПЗУ, ТУ и геоподоснова для демо-портала."]),
                ],
                "other": [
                    ("01_Проектная документация/Состав томов.pdf", "Aurora | Состав томов", ["Разделы ПД по сделке Aurora."]),
                    ("02_Переписка/Письмо заказчика.docx", "Aurora | Переписка", ["Уточнение сроков выдачи и состава разделов."]),
                ],
                "results": [
                    ("01_Комплект ПД/Пояснительная записка.pdf", "Aurora | ПД", ["Передаваемый комплект проектной документации."]),
                    ("02_Результаты проверки/Лист замечаний.pdf", "Aurora | Проверка", ["Тестовый лист замечаний по комплекту ПД."]),
                ],
            },
        ),
        (
            "vector",
            {
                "tz": [
                    ("01_ТЗ_Vector.pdf", "Vector | ТЗ", ["Техническое задание на инженерные системы дата-центра."]),
                ],
                "other": [
                    ("01_Документация/Реестр разделов.docx", "Vector | Реестр разделов", ["Перечень разделов и исполнителей."]),
                ],
                "results": [
                    ("01_РД/Электроснабжение.pdf", "Vector | РД ЭОМ", ["Рабочая документация по системе электроснабжения."]),
                ],
            },
        ),
        (
            "polar",
            {
                "tz": [
                    ("01_ТЗ_Polar.pdf", "Polar | ТЗ", ["Техническое задание на транспортно-логистический терминал."]),
                ],
                "other": [
                    ("01_Исходные данные/Инженерные изыскания.pdf", "Polar | Изыскания", ["Базовые материалы по объекту Polar."]),
                ],
                "results": [
                    ("01_Генеральный план/ГП.pdf", "Polar | Генплан", ["Выданный комплект генерального плана."]),
                ],
            },
        ),
    ]

    for deal_key, sections in deal_storage_specs:
        deal = state.deals[deal_key]
        roots = local_entity_roots(str(deal.id), deal.title)
        for root in roots.values():
            root.mkdir(parents=True, exist_ok=True)
        for section_key, entries in sections.items():
            root = roots[section_key]
            for rel_name, title, paragraphs in entries:
                target = root / rel_name
                if target.suffix.lower() == ".pdf":
                    write_abs_bytes(target, make_pdf_bytes(title, paragraphs))
                elif target.suffix.lower() == ".docx":
                    write_abs_bytes(target, make_docx_bytes(title, paragraphs))
                else:
                    write_abs_text(target, "\n".join([title, *paragraphs]))

    card_storage_specs = [
        (
            "aurora_geo",
            {
                "tz": [
                    ("01_ТЗ_Субподряд.pdf", "TestGeo | ТЗ", ["ТЗ на геоподоснову и изыскания Aurora."]),
                ],
                "other": [
                    ("01_Иные/Лицензия.pdf", "TestGeo | Лицензия", ["Тестовая лицензия исполнителя."]),
                ],
                "results": [
                    ("01_Результаты/Геоподоснова.pdf", "TestGeo | Геоподоснова", ["Итоговый комплект геоподосновы."]),
                ],
            },
        ),
        (
            "aurora_fire",
            {
                "tz": [
                    ("01_ТЗ_ПБ.pdf", "Fireline | ТЗ", ["Задание на мероприятия по пожарной безопасности."]),
                ],
                "other": [
                    ("01_Иные/Реестр замечаний.docx", "Fireline | Замечания", ["Реестр замечаний ГИПа к СПЗ."]),
                ],
                "results": [
                    ("01_Результаты/СПЗ.pdf", "Fireline | СПЗ", ["Передаваемый комплект пожарной безопасности."]),
                ],
            },
        ),
        (
            "vector_hvac",
            {
                "tz": [
                    ("01_ТЗ_ОВК.pdf", "Delta HVAC | ТЗ", ["Задание на ОВК и ИТП для Vector."]),
                ],
                "other": [
                    ("01_Иные/Сводка решений.pdf", "Delta HVAC | Сводка решений", ["Предварительная сводка инженерных решений."]),
                ],
                "results": [
                    ("01_Результаты/ОВК.pdf", "Delta HVAC | ОВК", ["Рабочий комплект по ОВК."]),
                ],
            },
        ),
    ]

    for card_key, sections in card_storage_specs:
        card = state.subcontractor_cards[card_key]
        roots = local_entity_roots(str(card.id), card.title)
        for root in roots.values():
            root.mkdir(parents=True, exist_ok=True)
        for section_key, entries in sections.items():
            root = roots[section_key]
            for rel_name, title, paragraphs in entries:
                target = root / rel_name
                if target.suffix.lower() == ".pdf":
                    write_abs_bytes(target, make_pdf_bytes(title, paragraphs))
                elif target.suffix.lower() == ".docx":
                    write_abs_bytes(target, make_docx_bytes(title, paragraphs))
                else:
                    write_abs_text(target, "\n".join([title, *paragraphs]))

    avatars = {
        "admin@nexus-demo.ru": "NT",
        "manager@nexus-demo.ru": "PM",
        "finance@nexus-demo.ru": "FN",
        "contracts@nexus-demo.ru": "CT",
        "customer@aurora-demo.ru": "AU",
        "customer@vector-demo.ru": "VE",
    }
    for email, initials in avatars.items():
        safe_name = email.replace("@", "_at_").replace(".", "_")
        avatar_path = STATIC_ROOT / "avatars" / f"{safe_name}.svg"
        write_abs_text(
            avatar_path,
            (
                "<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"96\" height=\"96\" viewBox=\"0 0 96 96\">"
                "<rect width=\"96\" height=\"96\" rx=\"24\" fill=\"#2563eb\"/>"
                f"<text x=\"48\" y=\"57\" text-anchor=\"middle\" font-family=\"Arial\" font-size=\"28\" fill=\"#ffffff\">{initials}</text>"
                "</svg>"
            ),
        )

    readme_assets = TEST_ROOT / "assets"
    readme_assets.mkdir(parents=True, exist_ok=True)
    write_abs_bytes(
        readme_assets / "nexus-logo-demo.pdf",
        make_pdf_bytes("Nexus Demo", ["Локальный тестовый портал", "Использовать только для демо и QA."]),
    )


def write_readme() -> None:
    content = f"""# Nexus Test Portal

Локальный тестовый контур CRM, изолированный от основной базы и основного файлового хранилища.

## Что создаётся

- База данных: `{DB_PATH}`
- Файловое хранилище: `{STORAGE_ROOT}`
- Статика: `{STATIC_ROOT}`
- Временные загрузки: `{TMP_ROOT}`

## Важно

- Этот контур **не деплоится на VPS**.
- Основные базы `{MAIN_DB_CANDIDATES[0].name}` / `{MAIN_DB_CANDIDATES[1].name}` не используются.
- Все бренды заменены на **Nexus**.

## Тестовые логины

- `admin@nexus-demo.ru` / `Nexus123!`
- `manager@nexus-demo.ru` / `Nexus123!`
- `finance@nexus-demo.ru` / `Nexus123!`
- `contracts@nexus-demo.ru` / `Nexus123!`
- `customer@aurora-demo.ru` / `Nexus123!`
- `customer@vector-demo.ru` / `Nexus123!`
- `geo.lead@testgeo-demo.ru` / `Nexus123!`
- `fire.lead@testfire-demo.ru` / `Nexus123!`
- `hvac.lead@delta-demo.ru` / `Nexus123!`

## Локальный запуск

Backend:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\\start_test_portal_backend.ps1
```

Frontend:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\\start_test_portal_frontend.ps1
```

Или сразу оба:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\\start_test_portal.ps1
```
"""
    README_PATH.write_text(content, encoding="utf-8")


def verify_main_dbs_unchanged(before_signatures: Dict[Path, Tuple[bool, int, int]]) -> None:
    after_signatures = {path: _path_signature(path) for path in MAIN_DB_CANDIDATES}
    changed = [
        str(path)
        for path in MAIN_DB_CANDIDATES
        if before_signatures.get(path) != after_signatures.get(path)
    ]
    if changed:
        raise RuntimeError(f"Main database signatures changed unexpectedly: {', '.join(changed)}")


def main() -> None:
    before_signatures = {path: _path_signature(path) for path in MAIN_DB_CANDIDATES}
    _prepare_test_root()
    bootstrap_database()
    state = seed_everything()
    populate_storage_roots(state)
    write_readme()
    verify_main_dbs_unchanged(before_signatures)
    print("Nexus test portal bootstrap completed.")
    print(f"Test DB: {DB_PATH}")
    print(f"Storage: {STORAGE_ROOT}")
    print(f"Static: {STATIC_ROOT}")
    print("Main databases unchanged.")


if __name__ == "__main__":
    main()
