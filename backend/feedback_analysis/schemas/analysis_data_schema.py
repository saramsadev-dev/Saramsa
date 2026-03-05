"""
Pydantic schema for normalized analysis data stored in analysisData.
"""

from typing import List, Any
from pydantic import BaseModel, ConfigDict


class SentimentBreakdown(BaseModel):
    positive: float
    negative: float
    neutral: float


class Counts(BaseModel):
    total: int
    positive: int
    negative: int
    neutral: int


class SampleComments(BaseModel):
    positive: List[str] = []
    negative: List[str] = []
    neutral: List[str] = []


class Feature(BaseModel):
    name: str
    description: str = ""
    sentiment: SentimentBreakdown
    keywords: List[str]
    comment_count: int = 0
    sample_comments: SampleComments | None = None


class AnalysisData(BaseModel):
    overall: SentimentBreakdown
    counts: Counts
    features: List[Feature]
    positive_keywords: List[Any] = []
    negative_keywords: List[Any] = []

    model_config = ConfigDict(extra="allow")


def validate_analysis_data(data: dict) -> AnalysisData:
    """Validate normalized analysis data and return parsed model."""
    return AnalysisData.model_validate(data)
