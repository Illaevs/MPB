from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
import httpx

from app.core.config import settings
from app.core.auth_middleware import CurrentUser
from app.models import User
from app.services.permissions import require_section_read
from app.services.dadata_parse import parse_party


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
    parsed = parse_party(data)

    # Fallback на suggestion.value, если DaData не дал короткое/полное имя.
    return {
        "short_name": parsed["short_name"] or suggestion.get("value"),
        "full_name": parsed["full_name"] or suggestion.get("value"),
        "kpp": parsed["kpp"],
        "ceo_name": parsed["ceo_name"],
        "director_last_name": parsed["director_last_name"],
        "director_first_name": parsed["director_first_name"],
        "director_middle_name": parsed["director_middle_name"],
        "director_position": parsed["director_position"],
        "is_individual": parsed["is_individual"],
        "opf_short": parsed["opf_short"],
        "address": parsed["address"],
    }
