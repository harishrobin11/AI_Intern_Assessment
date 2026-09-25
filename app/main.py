import os
from typing import Optional, List, Dict, Any
from contextlib import asynccontextmanager
import pandas as pd
from fastapi import FastAPI, Depends, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.schemas import (
    HealthResponse, SummaryResponse, QueryRequest, QueryResponse, AnomalyResponse
)
from app.dependencies import (
    get_data_service, get_query_service, get_anomaly_service
)
from app.services.data_service import DataService
from app.services.query_service import QueryService
from app.services.anomaly_service import AnomalyService
from app.utils.logging_config import logger

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing SupportIQ application startup...")
    ds = get_data_service()
    try:
        df = ds.load_data()
        logger.info(f"Loaded dataset with {len(df)} records.")
    except Exception as e:
        logger.error(f"Startup data loading failure: {e}")
    yield

app = FastAPI(
    title="SupportIQ API",
    description="AI-Powered Customer Support Ticket Analytics & Anomaly Detection System",
    version="1.0.0",
    lifespan=lifespan
)

# Enable CORS for Streamlit / Frontend interaction
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/", include_in_schema=False)
def root():
    return {
        "message": "Welcome to SupportIQ API",
        "health_check": "/health",
        "docs": "/docs"
    }

@app.get("/health", response_model=HealthResponse, tags=["Health"])
def get_health(ds: DataService = Depends(get_data_service)):
    health_info = ds.get_health_status()
    groq_key_set = bool(settings.GROQ_API_KEY and not settings.GROQ_API_KEY.startswith("replace_with"))
    
    return HealthResponse(
        status="healthy" if health_info["file_exists"] else "unhealthy",
        dataset_path=health_info["dataset_path"],
        file_exists=health_info["file_exists"],
        row_count=health_info["row_count"],
        groq_configured=groq_key_set,
        groq_model=settings.GROQ_MODEL
    )

@app.get("/summary", response_model=SummaryResponse, tags=["Analytics"])
def get_summary(ds: DataService = Depends(get_data_service)):
    try:
        stats = ds.get_summary_stats()
        return SummaryResponse(**stats)
    except Exception as e:
        logger.error(f"Error generating summary stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate dataset summary: {str(e)}"
        )

@app.post("/query", response_model=QueryResponse, tags=["Natural Language Query"])
def process_natural_language_query(
    request: QueryRequest,
    qs: QueryService = Depends(get_query_service)
):
    if not request.question or not request.question.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Question string cannot be empty."
        )

    try:
        response = qs.process_query(request.question)
        return response
    except Exception as e:
        logger.error(f"Unhandled error processing query '{request.question}': {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while evaluating your question."
        )

@app.get("/anomalies", response_model=AnomalyResponse, tags=["Anomaly Detection"])
def get_anomalies(
    anomaly_type: Optional[str] = Query(None, description="Filter by anomaly type e.g. critical_unresolved, resolution_time_outlier"),
    severity: Optional[str] = Query(None, description="Filter by severity e.g. critical, high, medium, low"),
    ans: AnomalyService = Depends(get_anomaly_service)
):
    try:
        return ans.detect_anomalies(anomaly_type_filter=anomaly_type, severity_filter=severity)
    except Exception as e:
        logger.error(f"Error detecting anomalies: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to detect dataset anomalies: {str(e)}"
        )

@app.get("/tickets", tags=["Ticket Explorer"])
def list_tickets(
    category: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    status_filter: Optional[str] = Query(None, alias="status"),
    agent_id: Optional[str] = Query(None),
    search: Optional[str] = Query(None, description="Search term in issue summary or ticket ID"),
    limit: int = Query(20, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    ds: DataService = Depends(get_data_service)
):
    try:
        df = ds.get_df().copy()
        
        if category:
            df = df[df["category"] == category]
        if priority:
            df = df[df["priority"] == priority]
        if status_filter:
            df = df[df["status"] == status_filter]
        if agent_id:
            df = df[df["agent_id"] == agent_id]
        if search:
            search_str = search.lower().strip()
            df = df[
                df["issue_summary"].str.lower().str.contains(search_str, na=False) |
                df["ticket_id"].str.lower().str.contains(search_str, na=False)
            ]

        total_count = len(df)
        paginated_df = df.iloc[offset : offset + limit]

        records = []
        for _, row in paginated_df.iterrows():
            records.append({
                "ticket_id": str(row["ticket_id"]),
                "created_at": row["created_at"].strftime("%Y-%m-%d %H:%M") if pd.notna(row["created_at"]) else None,
                "category": str(row["category"]),
                "priority": str(row["priority"]),
                "status": str(row["status"]),
                "response_time_hrs": float(row["response_time_hrs"]) if pd.notna(row["response_time_hrs"]) else None,
                "resolution_time_hrs": float(row["resolution_time_hrs"]) if pd.notna(row["resolution_time_hrs"]) else None,
                "agent_id": str(row["agent_id"]),
                "customer_rating": float(row["customer_rating"]) if pd.notna(row["customer_rating"]) else None,
                "issue_summary": str(row["issue_summary"])
            })

        return {
            "total": total_count,
            "limit": limit,
            "offset": offset,
            "tickets": records
        }
    except Exception as e:
        logger.error(f"Error fetching tickets: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch tickets: {str(e)}"
        )
