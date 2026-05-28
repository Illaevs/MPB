from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import httpx

from app.core.config import settings


router = APIRouter()


class BankLookupRequest(BaseModel):
    query: str


@router.post("/banks/lookup")
async def lookup_bank(request: BankLookupRequest):
    token = settings.DADATA_TOKEN
    if not token:
        raise HTTPException(status_code=500, detail="Dadata token is not configured")

    query = request.query.strip()
    if not query:
        raise HTTPException(status_code=400, detail="Query is required")

    url = "https://suggestions.dadata.ru/suggestions/api/4_1/rs/findById/bank"
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Authorization": f"Token {token}",
    }

    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.post(url, json={"query": query}, headers=headers)

    if response.status_code >= 400:
        raise HTTPException(status_code=502, detail="Failed to lookup bank data")

    payload = response.json()
    suggestions = payload.get("suggestions") or []
    if not suggestions:
        return {}

    suggestion = suggestions[0]
    data = suggestion.get("data") or {}
    name = (data.get("name") or {}).get("payment") or (data.get("name") or {}).get("short") or suggestion.get("value")

    return {
        "bank_name": name,
        "correspondent_account": data.get("correspondent_account"),
        "bik": data.get("bic"),
        "swift": data.get("swift"),
    }
