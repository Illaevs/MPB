from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
import httpx

from app.core.config import settings
from app.core.auth_middleware import CurrentUser
from app.models import User
from app.services.permissions import require_section_read


router = APIRouter()


class PartyLookupRequest(BaseModel):
    query: str


@router.post("/dadata/party")
async def lookup_party(
    request: PartyLookupRequest,
    _: User = Depends(CurrentUser),
    __=Depends(require_section_read("companies")),
):
    token = settings.DADATA_TOKEN
    if not token:
        raise HTTPException(status_code=500, detail="Dadata token is not configured")

    query = request.query.strip()
    if not query:
        raise HTTPException(status_code=400, detail="Query is required")

    url = "https://suggestions.dadata.ru/suggestions/api/4_1/rs/findById/party"
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Authorization": f"Token {token}",
    }

    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.post(url, json={"query": query, "branch_type": "MAIN"}, headers=headers)

    if response.status_code >= 400:
        raise HTTPException(status_code=502, detail="Failed to lookup party data")

    payload = response.json()
    suggestions = payload.get("suggestions") or []
    if not suggestions:
        return {}

    suggestion = suggestions[0]
    data = suggestion.get("data") or {}
    name_data = data.get("name") or {}
    short_name = name_data.get("short_with_opf") or name_data.get("short") or suggestion.get("value")
    full_name = name_data.get("full_with_opf") or name_data.get("full") or suggestion.get("value")

    ceo_name = None
    management = data.get("management") or {}
    if management.get("name"):
        ceo_name = management.get("name")
    else:
        fio = data.get("fio") or {}
        fio_parts = [fio.get("surname"), fio.get("name"), fio.get("patronymic")]
        fio_value = " ".join([part for part in fio_parts if part])
        if fio_value:
            ceo_name = fio_value

    address = None
    address_data = data.get("address") or {}
    if address_data.get("value"):
        address = address_data.get("value")

    return {
        "short_name": short_name,
        "full_name": full_name,
        "kpp": data.get("kpp"),
        "ceo_name": ceo_name,
        "address": address,
    }
