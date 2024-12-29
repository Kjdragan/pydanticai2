from typing import Dict, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field

class TavilyResult(BaseModel):
    """Selective model of Tavily result - only fields we need"""
    url: str
    title: str
    content: str  # The focused/relevant content
    raw_content: Optional[str] = None  # Full article text
    published_date: Optional[str] = None

class EvaluationOutput(BaseModel):
    """LLM evaluation response structure"""
    is_valid: bool
    source: Optional[str] = None  # Only populated if is_valid=True
    reason: str  # e.g., "too short", "mainly html", "empty data", "valid article"

class ContentForJudging(BaseModel):
    """Our internal representation for judging"""
    id: str
    query: str
    raw_content: str
    url: str  # Keep URL for LLM to help determine source
    title: str  # Title can help LLM identify source context
    metadata: Dict[str, str] = Field(default_factory=dict)

class ValidResult(BaseModel):
    """Structure for content that passes evaluation"""
    url: str
    title: str
    source: str  # As determined by LLM
    focused_content: str
    raw_content: str
    published_date: Optional[str] = None
    query: str
    evaluation_reason: str  # Keep the reason even for valid results

class QueryResults(BaseModel):
    """Group results by query"""
    query: str
    valid_results: List[ValidResult] = Field(default_factory=list)
    total_evaluated: int = 0
    total_passed: int = 0
    failure_reasons: Dict[str, int] = Field(default_factory=dict)  # Track counts of different failure reasons