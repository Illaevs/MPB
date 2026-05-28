"""
Pydantic schemas for AI assistant endpoints.
"""
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field

from app.schemas.outgoing_document import OutgoingDocumentResolveRequest


class AiStatusResponse(BaseModel):
    enabled: bool
    provider: str = "ollama"
    model: Optional[str] = None
    reachable: bool = False
    detail: Optional[str] = None


class OutgoingAiAssistRequest(BaseModel):
    action: Literal["draft", "improve", "formalize", "shorten"]
    prompt: Optional[str] = ""
    current_html: Optional[str] = ""
    selection_text: Optional[str] = ""
    selection_present: bool = False
    document_payload: OutgoingDocumentResolveRequest


class OutgoingAiAssistResponse(BaseModel):
    action: str
    model: str
    html: str
    text: str
    used_fields: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    summary: Optional[str] = None
    raw: Optional[Any] = None


class AiAssistantMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str
    used_deal_ids: List[str] = Field(default_factory=list)
    used_sections: List[str] = Field(default_factory=list)


class AiAssistantPageContext(BaseModel):
    route_name: Optional[str] = None
    path: Optional[str] = None
    section: Optional[str] = None
    entity_type: Optional[str] = None
    entity_id: Optional[str] = None
    params: Dict[str, Any] = Field(default_factory=dict)
    query: Dict[str, Any] = Field(default_factory=dict)


class AiAssistantChatRequest(BaseModel):
    message: str
    history: List[AiAssistantMessage] = Field(default_factory=list)
    page_context: Optional[AiAssistantPageContext] = None


class AiAssistantChatResponse(BaseModel):
    answer: str
    model: str
    warnings: List[str] = Field(default_factory=list)
    used_deal_ids: List[str] = Field(default_factory=list)
    used_sections: List[str] = Field(default_factory=list)
    raw: Optional[Any] = None
