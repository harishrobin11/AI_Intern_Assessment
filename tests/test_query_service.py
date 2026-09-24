import pytest
from unittest.mock import MagicMock
from app.schemas import QueryPlan, QueryResponse
from app.services.data_service import DataService
from app.services.analytics_service import AnalyticsService
from app.services.query_service import QueryService, SUPPORTED_SCOPE_MESSAGE

@pytest.fixture
def mock_query_service(tmp_path):
    csv_file = tmp_path / "tickets_sample.csv"
    csv_content = (
        "ticket_id,created_at,category,priority,status,response_time_hrs,resolution_time_hrs,agent_id,customer_rating,issue_summary\n"
        "TKT-001,2024-01-03 09:12,Billing,High,Resolved,0.5,2.3,AGT-04,4.0,Incorrect charge on invoice\n"
        "TKT-002,2024-01-03 11:45,Technical,Critical,Escalated,1.2,,AGT-07,,Login failure after update\n"
        "TKT-003,2024-01-04 08:30,General,Low,Resolved,3.1,5.0,AGT-02,5.0,Request for product docs\n"
        "TKT-004,2024-01-04 14:22,Technical,High,Resolved,0.8,4.7,AGT-04,3.0,API timeout in production\n"
    )
    csv_file.write_text(csv_content)

    ds = DataService(csv_path=str(csv_file))
    ds.load_data()
    analytics = AnalyticsService(ds=ds)
    mock_llm = MagicMock()
    return QueryService(llm=mock_llm, analytics=analytics)

def test_query_service_count(mock_query_service):
    mock_plan = QueryPlan(
        operation="count",
        filters={"status": ["Open", "Escalated"]},
        explanation="Count unresolved tickets"
    )
    mock_query_service.llm.generate_query_plan.return_value = mock_plan

    response = mock_query_service.process_query("How many tickets are unresolved?")
    assert isinstance(response, QueryResponse)
    assert response.query_plan.operation == "count"
    assert response.result["value"] == 1
    assert "There is 1 ticket matching your request" in response.answer
    assert len(response.evidence) == 1
    assert response.evidence[0]["ticket_id"] == "TKT-002"

def test_query_service_average(mock_query_service):
    mock_plan = QueryPlan(
        operation="average",
        metric="customer_rating",
        filters={"category": "Billing"},
        explanation="Average customer rating for Billing tickets"
    )
    mock_query_service.llm.generate_query_plan.return_value = mock_plan

    response = mock_query_service.process_query("What is the average rating for Billing tickets?")
    assert response.result["value"] == 4.0
    assert "The average customer rating" in response.answer
    assert "4.0" in response.answer

def test_query_service_unsupported(mock_query_service):
    mock_plan = QueryPlan(
        operation="unsupported",
        explanation="Cannot forecast stock prices."
    )
    mock_query_service.llm.generate_query_plan.return_value = mock_plan

    response = mock_query_service.process_query("What will the stock price be tomorrow?")
    assert response.query_plan.operation == "unsupported"
    assert "Cannot forecast stock prices" in response.answer
    assert SUPPORTED_SCOPE_MESSAGE in response.answer
    assert response.evidence == []
