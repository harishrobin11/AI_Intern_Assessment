from typing import Dict, Any, List, Optional, Literal
from pydantic import BaseModel, Field, field_validator

class QueryPlan(BaseModel):
    operation: Literal[
        "count", "average", "sum", "min", "max",
        "group_count", "group_average", "top_n",
        "filter", "list_records", "unsupported"
    ] = Field(..., description="Target analytical operation")
    metric: Optional[str] = Field(None, description="Metric field for numerical aggregations")
    group_by: Optional[str] = Field(None, description="Dimension field for grouping or ranking")
    filters: Dict[str, Any] = Field(default_factory=dict, description="Filter dictionary")
    limit: int = Field(20, ge=1, le=100, description="Max result count")
    sort_order: str = Field("desc", description="Sorting direction: asc or desc")
    explanation: Optional[str] = Field(None, description="Reasoning or description of plan")

    @field_validator("limit")
    @classmethod
    def cap_limit(cls, v: int) -> int:
        return min(max(v, 1), 100)

class QueryRequest(BaseModel):
    question: str = Field(..., min_length=2, max_length=500, json_schema_extra={"example": "What is the average customer rating for Technical tickets?"})

class QueryResponse(BaseModel):
    question: str
    query_plan: QueryPlan
    result: Dict[str, Any]
    answer: str
    evidence: List[Dict[str, Any]] = Field(default_factory=list)

class Anomaly(BaseModel):
    ticket_id: str
    anomaly_type: str
    severity: Literal["low", "medium", "high", "critical"]
    reason: str
    detected_value: Optional[Any] = None
    threshold: Optional[Any] = None

class AnomalyResponse(BaseModel):
    total_anomalies: int
    anomalies: List[Anomaly]

class HealthResponse(BaseModel):
    status: str
    dataset_path: str
    file_exists: bool
    row_count: int
    groq_configured: bool
    groq_model: str

class SummaryResponse(BaseModel):
    total_tickets: int
    unresolved_tickets: int
    critical_unresolved_tickets: int
    status_counts: Dict[str, int]
    priority_counts: Dict[str, int]
    category_counts: Dict[str, int]
    avg_response_time_hrs: Optional[float] = None
    avg_resolution_time_hrs: Optional[float] = None
    avg_customer_rating: Optional[float] = None
