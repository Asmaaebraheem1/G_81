"""AI assistant, insights, summary, conversations, and flags."""

from __future__ import annotations

from flask_jwt_extended import jwt_required

from app.api.v1.blueprint import TAG_AI, api_v1
from app.api.v1.deps import current_user
from app.api.v1.schemas import ChatBody, FlagBody, IdPath, InsightsBody, SummaryBody
from app.core.errors import success
from app.modules.ai import service


@api_v1.get("/ai/status", tags=[TAG_AI], summary="AI availability and budget")
@jwt_required()
def ai_status():
    return success(service.status(current_user()))


@api_v1.post("/ai/chat", tags=[TAG_AI], summary="Grounded assistant answer")
@jwt_required()
def ai_chat(body: ChatBody):
    return success(service.chat(current_user(), body))


@api_v1.get("/ai/conversations", tags=[TAG_AI], summary="Conversation list")
@jwt_required()
def ai_conversations():
    return success(service.list_conversations(current_user()))


@api_v1.get("/ai/conversations/<int:id>", tags=[TAG_AI], summary="Conversation messages")
@jwt_required()
def ai_conversation_detail(path: IdPath):
    return success(service.get_conversation(current_user(), path.id))


@api_v1.delete("/ai/conversations/<int:id>", tags=[TAG_AI], summary="Delete conversation")
@jwt_required()
def ai_conversation_delete(path: IdPath):
    return success(service.delete_conversation(current_user(), path.id))


@api_v1.post("/ai/insights", tags=[TAG_AI], summary="Report insights")
@jwt_required()
def ai_insights(body: InsightsBody):
    return success(service.insights(current_user(), body))


@api_v1.post("/ai/summary", tags=[TAG_AI], summary="Sustainability summary")
@jwt_required()
def ai_summary(body: SummaryBody):
    return success(service.summary(current_user(), body))


@api_v1.post("/ai/flag", tags=[TAG_AI], summary="Report an AI response")
@jwt_required()
def ai_flag(body: FlagBody):
    return success(service.flag_response(current_user(), body), 201)
