from __future__ import annotations

from datetime import datetime
from html import escape
from io import BytesIO
from typing import Iterable, Optional

from fastapi.concurrency import run_in_threadpool
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.data_health import get_grouped_health_issues, get_health_issues


def _label_severity(value: str | None) -> str:
    if value == "error":
        return "Ошибка"
    if value == "warning":
        return "Предупреждение"
    return "Инфо"


def _label_module(value: str | None) -> str:
    labels = {
        "projects": "Сделки",
        "stages": "Этапы",
        "contracting": "Контрактация",
        "contracts": "Договоры",
        "outgoing": "Письма",
    }
    return labels.get(value or "", value or "Прочее")


def _format_datetime(value) -> str:
    if not value:
        return ""
    if isinstance(value, str):
        return value[:16].replace("T", " ")
    if isinstance(value, datetime):
        return value.strftime("%d.%m.%Y %H:%M")
    return str(value)


def _report_html(*, issues: list[dict], summary: dict, grouped: bool) -> str:
    generated_at = datetime.now().strftime("%d.%m.%Y %H:%M")
    rows = []
    for item in issues:
        count = int(item.get("count") or 1)
        meta = []
        if item.get("deal_title"):
            meta.append(f"Сделка: {escape(str(item.get('deal_title')))}")
        payload = item.get("payload") or {}
        if payload.get("stage_name"):
            meta.append(f"Этап: {escape(str(payload.get('stage_name')))}")
        if payload.get("product_name"):
            meta.append(f"Товар: {escape(str(payload.get('product_name')))}")
        if payload.get("contract_number"):
            meta.append(f"Договор: {escape(str(payload.get('contract_number')))}")
        if payload.get("outgoing_number"):
            meta.append(f"Письмо: {escape(str(payload.get('outgoing_number')))}")
        count_badge = f"<span class=\"count\">{count} шт.</span>" if grouped and count > 1 else ""
        rows.append(
            f"""
            <tr>
                <td class="severity severity-{escape(str(item.get('severity') or 'info'))}">{escape(_label_severity(item.get('severity')))}</td>
                <td>{escape(_label_module(item.get('module')))}</td>
                <td>
                    <div class="title">{escape(str(item.get('title') or ''))} {count_badge}</div>
                    <div class="description">{escape(str(item.get('description') or ''))}</div>
                    <div class="meta">{' | '.join(meta)}</div>
                </td>
                <td>{escape(_format_datetime(item.get('last_detected_at') or item.get('first_detected_at')))}</td>
            </tr>
            """
        )

    if not rows:
        rows.append('<tr><td colspan="4" class="empty">Активных проблем не найдено</td></tr>')

    return f"""
    <!doctype html>
    <html>
    <head>
      <meta charset="utf-8">
      <style>
        @font-face {{
          font-family: DejaVuSans;
          src: url("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf");
        }}
        body {{
          font-family: DejaVuSans, sans-serif;
          color: #111827;
          font-size: 10px;
        }}
        h1 {{
          margin: 0 0 4px;
          font-size: 18px;
        }}
        .subtitle {{
          color: #6b7280;
          margin-bottom: 14px;
        }}
        .summary {{
          width: 100%;
          margin-bottom: 14px;
          border-collapse: collapse;
        }}
        .summary td {{
          padding: 8px;
          border: 1px solid #dbe3ef;
          background: #f8fafc;
        }}
        .summary .value {{
          display: block;
          font-size: 16px;
          font-weight: 700;
          margin-top: 2px;
        }}
        table.issues {{
          width: 100%;
          border-collapse: collapse;
        }}
        .issues th {{
          text-align: left;
          background: #eef2f7;
          border: 1px solid #dbe3ef;
          padding: 7px;
          font-weight: 700;
        }}
        .issues td {{
          vertical-align: top;
          border: 1px solid #dbe3ef;
          padding: 7px;
        }}
        .severity {{
          font-weight: 700;
          white-space: nowrap;
        }}
        .severity-error {{
          color: #dc2626;
        }}
        .severity-warning {{
          color: #b45309;
        }}
        .severity-info {{
          color: #2563eb;
        }}
        .title {{
          font-weight: 700;
          margin-bottom: 3px;
        }}
        .description {{
          color: #334155;
          margin-bottom: 3px;
        }}
        .meta {{
          color: #64748b;
        }}
        .count {{
          color: #2563eb;
          font-weight: 700;
        }}
        .empty {{
          text-align: center;
          color: #64748b;
          padding: 18px;
        }}
      </style>
    </head>
    <body>
      <h1>Отчет контроля данных</h1>
      <div class="subtitle">Сформировано: {escape(generated_at)}</div>
      <table class="summary">
        <tr>
          <td>Всего<span class="value">{int(summary.get("total") or 0)}</span></td>
          <td>Ошибки<span class="value">{int(summary.get("errors") or 0)}</span></td>
          <td>Предупреждения<span class="value">{int(summary.get("warnings") or 0)}</span></td>
          <td>Игнор<span class="value">{int(summary.get("ignored") or 0)}</span></td>
        </tr>
      </table>
      <table class="issues">
        <thead>
          <tr>
            <th style="width: 14%;">Критичность</th>
            <th style="width: 14%;">Модуль</th>
            <th>Проблема</th>
            <th style="width: 15%;">Обновлено</th>
          </tr>
        </thead>
        <tbody>
          {''.join(rows)}
        </tbody>
      </table>
    </body>
    </html>
    """


def _html_to_pdf(html: str) -> bytes:
    try:
        from xhtml2pdf import pisa
    except Exception as exc:  # pragma: no cover
        raise RuntimeError("PDF generator is not installed") from exc

    output = BytesIO()
    result = pisa.CreatePDF(html, dest=output, encoding="UTF-8")
    if result.err:
        raise RuntimeError("Failed to generate data health PDF")
    return output.getvalue()


async def build_data_health_report_pdf(
    db: AsyncSession,
    *,
    deal_id: Optional[str] = None,
    allowed_deal_ids: Optional[Iterable[str]] = None,
    severity: Optional[str] = None,
    issue_type: Optional[str] = None,
    module: Optional[str] = None,
    status: str = "active",
    search: Optional[str] = None,
    grouped: bool = True,
    limit: int = 1000,
) -> bytes:
    if grouped:
        data = await get_grouped_health_issues(
            db,
            deal_id=deal_id,
            allowed_deal_ids=allowed_deal_ids,
            severity=severity,
            issue_type=issue_type,
            module=module,
            status=status,
            search=search,
            offset=0,
            limit=limit,
        )
    else:
        data = await get_health_issues(
            db,
            deal_id=deal_id,
            allowed_deal_ids=allowed_deal_ids,
            severity=severity,
            issue_type=issue_type,
            module=module,
            status=status,
            search=search,
            offset=0,
            limit=limit,
        )
    html = _report_html(issues=data.get("items") or [], summary=data.get("summary") or {}, grouped=grouped)
    # Synchronous xhtml2pdf render — offload so it doesn't block the loop.
    return await run_in_threadpool(_html_to_pdf, html)
