"""
Разбор ответа DaData findById/party в плоский словарь для формы/refresh.

Извлекает структурированного руководителя (ЕИО): Фамилия/Имя/Отчество +
должность. Покрывает оба случая:
  - юрлицо: data.management.name — одна строка «ФАМИЛИЯ ИМЯ ОТЧЕСТВО»,
    режем по пробелам (фамилия = 1-й токен, имя = 2-й, отчество = остаток);
    должность = data.management.post.
  - ИП: data.fio = {surname, name, patronymic} — уже структурировано;
    должность = «Индивидуальный предприниматель».

Возвращает также ceo_name (собранное ФИО) для обратной совместимости со
старым полем contact_person и шаблонами документов.
"""
from typing import Any, Dict, Optional


def _clean(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def parse_party(data: Dict[str, Any]) -> Dict[str, Any]:
    data = data or {}
    name_data = data.get("name") or {}
    management = data.get("management") or {}
    fio = data.get("fio") or {}
    opf = data.get("opf") or {}

    # ИП определяем по типу ОПФ или по наличию структурного fio.
    is_individual = (opf.get("type") == "INDIVIDUAL") or bool(
        fio.get("surname") or fio.get("name")
    )

    last = first = middle = None
    position: Optional[str] = None

    if fio.get("surname") or fio.get("name"):
        # ИП — данные уже разложены DaData.
        last = _clean(fio.get("surname"))
        first = _clean(fio.get("name"))
        middle = _clean(fio.get("patronymic"))
        position = "Индивидуальный предприниматель"
    elif management.get("name"):
        # Юрлицо — ФИО директора одной строкой, режем по пробелам.
        parts = [p for p in str(management["name"]).split() if p]
        if parts:
            last = _clean(parts[0])
            first = _clean(parts[1]) if len(parts) > 1 else None
            middle = _clean(" ".join(parts[2:])) if len(parts) > 2 else None
        position = _clean(management.get("post"))

    ceo_name = " ".join([p for p in [last, first, middle] if p]) or _clean(
        management.get("name")
    )

    return {
        "short_name": name_data.get("short_with_opf") or name_data.get("short"),
        "full_name": name_data.get("full_with_opf") or name_data.get("full"),
        "kpp": data.get("kpp"),
        "ceo_name": ceo_name,
        "director_last_name": last,
        "director_first_name": first,
        "director_middle_name": middle,
        "director_position": position,
        "is_individual": is_individual,
        "opf_short": _clean(opf.get("short")),  # «ООО», «ИП», «АО»...
        "address": (data.get("address") or {}).get("value"),
    }
