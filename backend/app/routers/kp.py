"""
API for commercial proposals (КП).
"""
import uuid
from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.core.config import settings
from app.models.kp import KpDocument, KpVersion, KpTemplate, KpTemplateBinding
from app.models.lead import Lead
from app.models.lead_product import LeadProduct
from app.schemas.kp import (
    KpDocumentCreate,
    KpDocumentResponse,
    KpVersionResponse,
    KpTemplateCreate,
    KpTemplateResponse,
    KpTemplateBindingCreate,
    KpTemplateBindingResponse,
)
from app.services.storage import upload_bytes_with_safe_extension, ensure_path, clean_name, read_file_bytes, publish
from app.utils.num2words_ru import num2text_rur
from app.core.auth_middleware import CurrentUser
from app.services.sequence_lock import sequence_lock
from app.services.kp_render import render_kp_docx, _fmt_money, _fmt_qty
from app.services.docx_to_pdf import convert_docx_bytes_to_pdf
from fastapi.concurrency import run_in_threadpool

router = APIRouter()


async def _next_kp_number(db: AsyncSession) -> int:
    result = await db.execute(select(func.max(KpDocument.number_seq)))
    max_val = result.scalar()
    if max_val is None:
        return settings.KP_NUMBER_START
    return int(max_val) + 1


def _format_kp_number(seq: int) -> str:
    return f"{seq}-КП"


async def _pick_template(db: AsyncSession, our_company_id: Optional[str], template_id: Optional[str]) -> Optional[KpTemplate]:
    if template_id:
        return await db.get(KpTemplate, template_id)
    if our_company_id:
        result = await db.execute(
            select(KpTemplate)
            .join(KpTemplateBinding, KpTemplateBinding.template_id == KpTemplate.id)
            .where(
                KpTemplateBinding.our_company_id == our_company_id,
                KpTemplate.is_active == 1,
            )
        )
        tpl = result.scalars().first()
        if tpl:
            return tpl
    # fallback to any active
    result = await db.execute(select(KpTemplate).where(KpTemplate.is_active == 1).order_by(KpTemplate.created_at))
    return result.scalars().first()


async def _render_and_save_version(
    db: AsyncSession,
    kp: KpDocument,
    template: Optional[KpTemplate],
    vat_rate: Optional[float] = None,
) -> KpVersion:
    """Создать новую версию КП и атомарно сохранить её файлы.

    Используется и при первичном создании КП (см. `create_kp`), и при
    ручном «Создать версию» из UI (см. `generate_kp_version_sync`).
    Раньше существовали ДВА разных пути:
      - `_generate_version` создавал KpVersion с totals, но БЕЗ файлов
        (поэтому v1 после `POST /kp/` была «заглушкой»);
      - `generate_kp_version_sync` рендерил DOCX+PDF, но был доступен
        только пользователю через отдельный клик.
    Этот helper унифицирует обе ветки: при наличии шаблона СРАЗУ
    рендерим файлы, сохраняем в storage и записываем URL'ы в БД.

    Args:
        db: открытая async-сессия. Эта функция делает `commit` внутри —
            нужна полностью отдельная транзакция (для storage I/O
            нежелательно держать БД-локи).
        kp: уже сохранённый KpDocument.
        template: KpTemplate или None — если None, версия создаётся
            «по-старому» без файлов (например, шаблон ещё не настроен).
        vat_rate: ставка НДС. Если None — берём `lead.vat_rate`,
            иначе 0. Используется только для подсчёта `vat_amount` —
            сам файл с per-line НДС товаров рендерится отдельно.
    """
    # === 1. Подсчёт сумм =================================================
    products = await LeadProduct.get_by_lead(db, kp.lead_id)
    total = sum(p.final_price or 0 for p in products)
    if vat_rate is None:
        lead = await db.get(Lead, kp.lead_id)
        vat_rate = float(getattr(lead, "vat_rate", 0.0) or 0.0)
    vat_amount = total * (float(vat_rate) / 100.0)
    total_text = num2text_rur(total)
    vat_text = num2text_rur(vat_amount)

    # === 2. Рендер файлов (если есть шаблон) ============================
    docx_href: Optional[str] = None
    pdf_href: Optional[str] = None
    version_num = (kp.current_version or 0) + 1

    if template and template.docx_url:
        try:
            template_bytes = await read_file_bytes(template.docx_url)
            context, products_ctx = await _build_kp_context_and_products(db, kp)
            docx_bytes = render_kp_docx(template_bytes, context, products_ctx)
            # PDF — опционально (soffice может отсутствовать локально).
            pdf_bytes = await run_in_threadpool(convert_docx_bytes_to_pdf, docx_bytes)

            folder = f"KP/{clean_name(kp.number_display or 'KP')}"
            await ensure_path(folder)
            base_name = f"{clean_name(kp.number_display or 'KP')}-v{version_num}"
            docx_path = f"{folder}/{base_name}.docx"
            pdf_path = f"{folder}/{base_name}.pdf"

            await upload_bytes_with_safe_extension(docx_path, docx_bytes)
            docx_href = await publish(docx_path)
            if pdf_bytes:
                await upload_bytes_with_safe_extension(pdf_path, pdf_bytes)
                pdf_href = await publish(pdf_path)
        except Exception as exc:
            # Не валим бизнес-операцию: пользователь увидит версию без
            # файлов и сможет нажать «Создать версию» вручную для retry.
            # Полный traceback оседает в логе backend.
            import logging
            logging.getLogger(__name__).exception(
                "KP render failed for kp=%s v%s: %s", kp.id, version_num, exc
            )

    # === 3. Создаём KpVersion с уже наполненными URL ====================
    version = KpVersion(
        kp_id=kp.id,
        version=version_num,
        docx_url=docx_href,
        pdf_url=pdf_href,
        total_amount=total,
        vat_amount=vat_amount,
        total_text=total_text,
        vat_text=vat_text,
        template_id=template.id if template else None,
    )
    db.add(version)
    kp.current_version = version_num
    kp.template_id = template.id if template else None
    kp.updated_at = datetime.now()
    await db.commit()
    await db.refresh(version)
    await db.refresh(kp)
    return version


# Старое имя — пусть продолжает работать как тонкий wrapper, чтобы не
# ломать никого, кто (вдруг) импортирует его из этого модуля.
async def _generate_version(
    db: AsyncSession,
    kp: KpDocument,
    template: Optional[KpTemplate],
    vat_rate: float,
) -> KpVersion:
    return await _render_and_save_version(db, kp, template, vat_rate=vat_rate)


@router.post("/kp/", response_model=KpDocumentResponse)
async def create_kp(
    payload: KpDocumentCreate,
    db: AsyncSession = Depends(get_db),
    _: CurrentUser = Depends(CurrentUser),
):
    lead = await db.get(Lead, payload.lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    # Resolve our_company_id: explicit payload → parent lead → system default.
    from app.services.our_company import get_default_id as _get_default_our_company_id
    resolved_our_company_id = (
        payload.our_company_id
        or lead.our_company_id
        or await _get_default_our_company_id(db)
    )
    tpl = await _pick_template(db, resolved_our_company_id, payload.template_id)

    # Serialize MAX(number_seq)+1 -> INSERT (number_seq has no UNIQUE
    # constraint, so a race would silently duplicate KP numbers).
    async with sequence_lock("kp_number"):
        seq = await _next_kp_number(db)
        number_display = _format_kp_number(seq)
        kp = KpDocument(
            lead_id=payload.lead_id,
            number_seq=seq,
            number_display=number_display,
            status="draft",
            current_version=0,
            our_company_id=resolved_our_company_id,
            template_id=tpl.id if tpl else None,
        )
        db.add(kp)
        await db.commit()
        await db.refresh(kp)

    # auto generate first version
    await _generate_version(db, kp, tpl, payload.vat_rate or 0)
    # Eager-load `versions` so the response model doesn't lazy-load it
    # outside the async context (MissingGreenlet 500).
    await db.refresh(kp, attribute_names=["versions"])
    return kp


@router.get("/kp/", response_model=List[KpDocumentResponse])
async def list_kp(
    lead_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    _: CurrentUser = Depends(CurrentUser),
):
    query = select(KpDocument).options(selectinload(KpDocument.versions))
    if lead_id:
        query = query.where(KpDocument.lead_id == lead_id)
    result = await db.execute(query.order_by(KpDocument.created_at.desc()))
    return result.scalars().all()


@router.post("/kp/{kp_id}/upload", response_model=KpVersionResponse)
async def upload_kp_version(
    kp_id: str,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    _: CurrentUser = Depends(CurrentUser),
):
    kp = await db.get(KpDocument, kp_id)
    if not kp:
        raise HTTPException(status_code=404, detail="KP not found")

    # prepare storage path
    folder = f"KP/{clean_name(kp.number_display)}"
    await ensure_path(folder)
    content = await file.read()
    safe_name = clean_name(file.filename or "kp.docx")
    file_path = f"{folder}/{safe_name}"
    # NB: upload_bytes_with_safe_extension сейчас (path: str, content: bytes)
    # и НЕ возвращает объект с public_url. Сохраняем file_path в БД,
    # отдача делается через get_download_href при скачивании.
    await upload_bytes_with_safe_extension(file_path, content)

    lead = await db.get(Lead, kp.lead_id)
    vat_rate = getattr(lead, "vat_rate", 0.0) or 0.0
    products = await LeadProduct.get_by_lead(db, kp.lead_id)
    total = sum(p.final_price or 0 for p in products)
    vat_amount = total * (vat_rate / 100.0)

    version_num = (kp.current_version or 0) + 1
    is_pdf = (file.filename or "").lower().endswith(".pdf")
    version = KpVersion(
        kp_id=kp.id,
        version=version_num,
        docx_url=None if is_pdf else file_path,
        pdf_url=file_path if is_pdf else None,
        template_id=kp.template_id,
        total_amount=total,
        vat_amount=vat_amount,
        total_text=num2text_rur(total),
        vat_text=num2text_rur(vat_amount),
    )
    db.add(version)
    kp.current_version = version_num
    kp.updated_at = datetime.now()
    await db.commit()
    await db.refresh(version)
    await db.refresh(kp)
    return version


@router.post("/kp/templates", response_model=KpTemplateResponse)
async def create_template(
    name: str = Form(...),
    docx: UploadFile = File(...),
    pdf: Optional[UploadFile] = File(None),
    db: AsyncSession = Depends(get_db),
    _: CurrentUser = Depends(CurrentUser),
):
    folder = f"KP/templates/{clean_name(name)}"
    await ensure_path(folder)

    docx_bytes = await docx.read()
    docx_name = clean_name(docx.filename or "template.docx")
    docx_path = f"{folder}/{docx_name}"
    await upload_bytes_with_safe_extension(docx_path, docx_bytes)

    pdf_path: Optional[str] = None
    if pdf:
        pdf_bytes = await pdf.read()
        pdf_name = clean_name(pdf.filename or "preview.pdf")
        pdf_path = f"{folder}/{pdf_name}"
        await upload_bytes_with_safe_extension(pdf_path, pdf_bytes)

    # `docx_url`/`pdf_url` в схеме называются *_url, но хранят storage-path
    # (как DocumentTemplateVersion.file_path). При скачивании путь
    # пропускается через get_download_href и превращается в реальный URL.
    tpl = KpTemplate(name=name, docx_url=docx_path, pdf_url=pdf_path, is_active=1)
    db.add(tpl)
    await db.commit()
    await db.refresh(tpl)
    return tpl


@router.get("/kp/templates", response_model=List[KpTemplateResponse])
async def list_templates(db: AsyncSession = Depends(get_db), _: CurrentUser = Depends(CurrentUser)):
    res = await db.execute(select(KpTemplate).order_by(KpTemplate.created_at.desc()))
    return res.scalars().all()


@router.post("/kp/template-bindings", response_model=KpTemplateBindingResponse)
async def bind_template(
    payload: KpTemplateBindingCreate,
    db: AsyncSession = Depends(get_db),
    _: CurrentUser = Depends(CurrentUser),
):
    tpl = await db.get(KpTemplate, payload.template_id)
    if not tpl:
        raise HTTPException(status_code=404, detail="Template not found")
    binding = KpTemplateBinding(template_id=payload.template_id, our_company_id=payload.our_company_id)
    db.add(binding)
    await db.commit()
    await db.refresh(binding)
    return binding


@router.get("/kp/template-bindings", response_model=List[KpTemplateBindingResponse])
async def list_bindings(db: AsyncSession = Depends(get_db), _: CurrentUser = Depends(CurrentUser)):
    res = await db.execute(select(KpTemplateBinding))
    return res.scalars().all()


@router.get("/kp/{kp_id}", response_model=KpDocumentResponse)
async def get_kp(kp_id: str, db: AsyncSession = Depends(get_db), _: CurrentUser = Depends(CurrentUser)):
    result = await db.execute(
        select(KpDocument).where(KpDocument.id == kp_id).options(selectinload(KpDocument.versions))
    )
    kp = result.scalar_one_or_none()
    if not kp:
        raise HTTPException(status_code=404, detail="KP not found")
    return kp


# ---------------------------------------------------------------------
# Серверный рендер docx-шаблона КП (вставляет настоящую таблицу товаров)
# ---------------------------------------------------------------------
_MONTHS_RU = [
    "января", "февраля", "марта", "апреля", "мая", "июня",
    "июля", "августа", "сентября", "октября", "ноября", "декабря",
]


def _format_kp_date(dt: Optional[datetime]) -> str:
    d = dt or datetime.now()
    dd = f"{d.day:02d}"
    return f"«{dd}» {_MONTHS_RU[d.month - 1]} {d.year} г."


async def _build_kp_context_and_products(db: AsyncSession, kp: KpDocument):
    """Подготовить (context, products) для render_kp_docx.

    Тянет последнюю версию КП (для total/vat сумм и текстовых представлений),
    лид, нашу компанию, заказчика и список товаров.
    """
    from app.models.company import Company
    from app.services.our_company import get_default_id as _get_default_our_company_id

    lead = await db.get(Lead, kp.lead_id) if kp.lead_id else None
    products_raw = await LeadProduct.get_by_lead(db, kp.lead_id) if kp.lead_id else []

    customer = await db.get(Company, lead.customer_id) if (lead and lead.customer_id) else None

    # Резолвим нашу компанию по цепочке: лид → КП → системный default.
    # Лиды до включения is_default могут иметь our_company_id = NULL,
    # а KP — нет (там autofill уже работает), поэтому fallback обязателен,
    # иначе все плейсхолдеры о «нашей компании» уходят пустыми.
    our_company_id = (
        (lead.our_company_id if lead else None)
        or kp.our_company_id
        or await _get_default_our_company_id(db)
    )
    our_company = await db.get(Company, our_company_id) if our_company_id else None

    # Берём latest version (она содержит суммы и прописью).
    versions = (await db.execute(
        select(KpVersion).where(KpVersion.kp_id == kp.id).order_by(KpVersion.version.desc()).limit(1)
    )).scalars().all()
    latest = versions[0] if versions else None
    # Если версии ещё нет (теоретически возможно) — посчитаем на лету.
    if latest:
        total_amount = float(latest.total_amount or 0)
        vat_amount = float(latest.vat_amount or 0)
        total_text = latest.total_text or ""
        vat_text = latest.vat_text or ""
    else:
        total_amount = sum(float(p.final_price or 0) for p in products_raw)
        # Эффективная средняя ставка из товаров.
        rates = [float(p.tax_rate or 0) for p in products_raw if p.tax_rate]
        avg_rate = (sum(rates) / len(rates)) if rates else 0.0
        vat_amount = total_amount * (avg_rate / 100.0)
        total_text = num2text_rur(total_amount)
        vat_text = num2text_rur(vat_amount)

    # Эффективная vat_rate для шапки: предпочитаем lead.vat_rate, иначе
    # средняя по товарам, иначе 22.
    rates = [int(p.tax_rate) for p in products_raw if p.tax_rate]
    eff_vat_rate = int(round(sum(rates) / len(rates))) if rates else (int(getattr(lead, "vat_rate", 0) or 22))

    # Помощник: достать ФИО руководителя/контакта из company.contacts[]
    # (если в первом контакте указан, например, position == 'Генеральный
    # директор') либо упасть в contact_person как самый общий случай.
    def _pick_director(company) -> str:
        if not company:
            return ""
        contacts = getattr(company, "contacts", None) or []
        # 1) Сначала ищем явно «директора» по позиции (рус/англ варианты).
        if isinstance(contacts, list):
            director_keywords = ("директ", "ген.дир", "генеральн", "director")
            for c in contacts:
                if not isinstance(c, dict):
                    continue
                pos = (c.get("position") or "").strip().lower()
                if pos and any(k in pos for k in director_keywords):
                    name = (c.get("name") or "").strip()
                    if name:
                        return name
            # 2) Иначе берём имя первого непустого контакта.
            for c in contacts:
                if isinstance(c, dict):
                    name = (c.get("name") or "").strip()
                    if name:
                        return name
        # 3) Fallback на contact_person.
        return (getattr(company, "contact_person", None) or "").strip()

    def _fio_to_initials(full_name: str) -> str:
        """«Фамилия Имя Отчество» → «И.О. Фамилия».

        Если на входе одно слово — отдаём как есть. Если уже в формате с
        точками (например «С.Н. Шатилов» или «Шатилов С.Н.») — не трогаем.
        Поддерживает двойные имена/фамилии через дефис (по первой букве
        каждой части): «Анна-Мария» → «А.». Игнорирует пустые токены.
        """
        if not full_name:
            return ""
        s = full_name.strip()
        if not s:
            return ""
        # Уже с точками — считаем, что инициалы есть.
        if "." in s:
            return s
        parts = [p for p in s.split() if p]
        if len(parts) == 1:
            return parts[0]
        surname, *rest = parts
        initials = []
        for p in rest:
            # Берём первую букву каждого куска, разделённого дефисом.
            sub = [chunk[:1].upper() for chunk in p.split("-") if chunk]
            if sub:
                initials.append(".".join(sub) + ".")
        if not initials:
            return surname
        return f"{''.join(initials)} {surname}"

    context = {
        # реквизиты КП
        "kp_number": kp.number_display or "",
        "kp_date": _format_kp_date(kp.created_at),
        "kp_validity_days": "30",
        # получатель
        "recipient_short_name": (customer.short_name or customer.name) if customer else "",
        "recipient_eio": _fio_to_initials(_pick_director(customer)),
        "recipient_to_name": (customer.short_name or customer.name) if customer else "",
        # объект
        "object_name": (lead.obj_name if lead else "") or "",
        "object_address": (lead.address if lead else "") or "",
        # финансы
        "total_amount": _fmt_money(total_amount),
        "total_amount_text": total_text,
        "vat_rate": str(eff_vat_rate),
        "vat_amount": _fmt_money(vat_amount),
        "vat_amount_text": vat_text,
        # Аванс в шаблоне всегда целым процентом (без .0): 5 → "5".
        # `or 0` ловит None; round() — на случай если в БД сохранилось
        # 5.0000001 после JSON-сериализации.
        "advance_percent": str(int(round(float(getattr(lead, "advance_percent", 0) or 0)))) if lead else "0",
        # наша компания
        "our_company_short_name": (our_company.short_name or our_company.name) if our_company else "",
        "our_company_director_position": "Генеральный директор",
        "our_company_director_name": _fio_to_initials(_pick_director(our_company)),
    }
    # Список товаров для настоящей docx-таблицы.
    products = []
    for idx, p in enumerate(products_raw, start=1):
        # Имя — custom_name, иначе подтянем из Product (если есть relationship).
        name = p.custom_name or (getattr(p.product, "name", None) if getattr(p, "product", None) else "") or ""
        products.append({
            "idx": idx,
            "name": name,
            "unit": p.unit or "",
            "qty": p.quantity or 0,
            "total": p.final_price or 0,
        })
    return context, products


@router.get("/kp/{kp_id}/render-docx")
async def render_kp_to_docx(
    kp_id: str,
    db: AsyncSession = Depends(get_db),
    _: CurrentUser = Depends(CurrentUser),
):
    """Серверный рендер docx КП:
      1) грузит шаблон по KpTemplate.docx_url (storage-path);
      2) подставляет все {plaсeholder}-маркеры;
      3) на месте {products_table} строит настоящую docx-таблицу;
      4) отдаёт готовый docx как поток.

    Фронт может либо скачать blob и тут же залить как новую версию
    (POST /uploads/kp/versions), либо использовать как preview.
    """
    from fastapi.responses import Response
    from sqlalchemy.orm import selectinload as _sl

    result = await db.execute(
        select(KpDocument).where(KpDocument.id == kp_id).options(_sl(KpDocument.versions))
    )
    kp = result.scalar_one_or_none()
    if not kp:
        raise HTTPException(status_code=404, detail="KP not found")
    if not kp.template_id:
        raise HTTPException(status_code=400, detail="KP has no template assigned")

    tpl = await db.get(KpTemplate, kp.template_id)
    if not tpl or not tpl.docx_url:
        raise HTTPException(status_code=400, detail="Template file is missing")

    try:
        template_bytes = await read_file_bytes(tpl.docx_url)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Template file not found in storage")
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to read template: {exc}")

    context, products = await _build_kp_context_and_products(db, kp)
    try:
        rendered = render_kp_docx(template_bytes, context, products)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to render docx: {exc}")

    filename = f"{kp.number_display or 'KP'}.docx"
    from urllib.parse import quote as _quote
    headers = {
        "Content-Disposition": f"attachment; filename*=UTF-8''{_quote(filename, safe='')}",
    }
    return Response(
        content=rendered,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers=headers,
    )


@router.post("/kp/{kp_id}/generate-version", response_model=KpVersionResponse)
async def generate_kp_version_sync(
    kp_id: str,
    db: AsyncSession = Depends(get_db),
    _: CurrentUser = Depends(CurrentUser),
):
    """Создать новую версию КП с DOCX (+ PDF если есть soffice).

    Тонкая обёртка над `_render_and_save_version` (тем же helper'ом,
    что используется при создании КП в `POST /kp/`). Гарантирует:
      • файлы создаются атомарно с записью KpVersion;
      • валидируем что шаблон существует, иначе явная 400-ошибка
        для фронта (вместо тихой версии без файлов).
    """
    kp = await db.get(KpDocument, kp_id)
    if not kp:
        raise HTTPException(status_code=404, detail="KP not found")
    if not kp.template_id:
        raise HTTPException(status_code=400, detail="У КП не выбран шаблон")

    tpl = await db.get(KpTemplate, kp.template_id)
    if not tpl or not tpl.docx_url:
        raise HTTPException(status_code=400, detail="Файл шаблона недоступен")

    # Проверяем доступность шаблона ДО вызова helper'а (он не падает,
    # а лишь логирует — для UX-разницы здесь нужно 4xx, а не «версия без
    # файлов»).
    try:
        await read_file_bytes(tpl.docx_url)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Файл шаблона не найден в storage")
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Не удалось прочитать шаблон: {exc}")

    return await _render_and_save_version(db, kp, tpl)
