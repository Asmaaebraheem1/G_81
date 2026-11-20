"""Validation models for structured AI output."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class AiBase(BaseModel):
    model_config = ConfigDict(extra="ignore")


class InsightAI(AiBase):
    narrative: str = Field(min_length=1, max_length=2000)
    observations: list[str] = Field(default_factory=list, max_length=6)
    opportunities: list[str] = Field(default_factory=list, max_length=6)


class SummaryAI(AiBase):
    narrative: str = Field(min_length=1, max_length=2000)
    highlights: list[str] = Field(default_factory=list, max_length=6)
    next_steps: list[str] = Field(default_factory=list, max_length=6)


class PlanActionAI(AiBase):
    title: str = Field(min_length=2, max_length=200)
    description: str = Field(default="", max_length=2000)
    category_key: str = Field(min_length=1, max_length=80)
    priority: Literal["high", "medium", "low"] = "medium"
    timeframe: Literal["this_week", "this_month", "this_quarter", "ongoing"] = "this_month"


class PlanAI(AiBase):
    title: str = Field(min_length=2, max_length=200)
    summary: str = Field(default="", max_length=4000)
    actions: list[PlanActionAI] = Field(min_length=1, max_length=8)


class AlternativeAI(AiBase):
    ordered_keys: list[str] = Field(min_length=1, max_length=20)
    rationale: str = Field(default="", max_length=1000)


class ExtractionAI(AiBase):
    vendor: str | None = Field(default=None, max_length=200)
    billing_period: str | None = Field(default=None, max_length=20)
    consumption_value: float | None = Field(default=None, ge=0, le=100000000)
    unit: str | None = Field(default=None, max_length=30)
    confidence: float = Field(default=0, ge=0, le=1)
