from app.services.data_service import data_service, DataService
from app.services.analytics_service import analytics_service, AnalyticsService
from app.services.llm_service import llm_service, LLMService
from app.services.query_service import query_service, QueryService
from app.services.anomaly_service import anomaly_service, AnomalyService

def get_data_service() -> DataService:
    return data_service

def get_analytics_service() -> AnalyticsService:
    return analytics_service

def get_llm_service() -> LLMService:
    return llm_service

def get_query_service() -> QueryService:
    return query_service

def get_anomaly_service() -> AnomalyService:
    return anomaly_service
