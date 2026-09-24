import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock
from app.main import app
from app.schemas import QueryPlan
from app.dependencies import get_query_service, get_data_service
from app.services.data_service import DataService
from app.services.query_service import QueryService
from app.services.analytics_service import AnalyticsService

@pytest.fixture
def client(tmp_path):
    csv_file = tmp_path / "api_tickets.csv"
    csv_content = (
        "ticket_id,created_at,category,priority,status,response_time_hrs,resolution_time_hrs,agent_id,customer_rating,issue_summary\n"
        "TKT-001,2024-01-03 09:12,Billing,High,Resolved,0.5,2.3,AGT-04,4.0,Incorrect charge on invoice\n"
        "TKT-002,2024-01-03 11:45,Technical,Critical,Escalated,1.2,,AGT-07,,Login failure after update\n"
    )
    csv_file.write_text(csv_content)

    ds = DataService(csv_path=str(csv_file))
    ds.load_data()
    analytics = AnalyticsService(ds=ds)

    mock_llm = MagicMock()
    mock_plan = QueryPlan(
        operation="count",
        filters={"status": ["Open", "Escalated"]},
        explanation="Count unresolved tickets"
    )
    mock_llm.generate_query_plan.return_value = mock_plan
    qs = QueryService(llm=mock_llm, analytics=analytics)

    app.dependency_overrides[get_data_service] = lambda: ds
    app.dependency_overrides[get_query_service] = lambda: qs

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()

def test_get_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["row_count"] == 2

def test_get_summary(client):
    response = client.get("/summary")
    assert response.status_code == 200
    data = response.json()
    assert data["total_tickets"] == 2
    assert data["unresolved_tickets"] == 1
    assert data["critical_unresolved_tickets"] == 1

def test_post_query_success(client):
    response = client.post("/query", json={"question": "How many critical tickets are unresolved?"})
    assert response.status_code == 200
    data = response.json()
    assert data["question"] == "How many critical tickets are unresolved?"
    assert data["query_plan"]["operation"] == "count"
    assert data["result"]["value"] == 1
    assert "answer" in data

def test_post_query_invalid_body(client):
    response = client.post("/query", json={"question": ""})
    # Fastapi validation or bad request check
    assert response.status_code in [400, 422]

def test_get_anomalies(client):
    response = client.get("/anomalies")
    assert response.status_code == 200
    data = response.json()
    assert "total_anomalies" in data
    assert "anomalies" in data

def test_get_tickets(client):
    response = client.get("/tickets?category=Billing")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["tickets"][0]["ticket_id"] == "TKT-001"
