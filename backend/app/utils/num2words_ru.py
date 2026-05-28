from __future__ import annotations

from num2words import num2words


def num2text_rur(value: float) -> str:
    """Return a Russian textual representation of a currency amount."""
    try:
        amount = round(float(value), 2)
    except (TypeError, ValueError):
        return str(value)
    try:
        return num2words(amount, lang="ru", to="currency", currency="RUB")
    except Exception:
        return str(amount)
