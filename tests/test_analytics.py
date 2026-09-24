import pytest
import pandas as pd
from app.services.data_service import DataService
from app.services.analytics_service import AnalyticsService

@pytest.fixture
def mock_analytics_service(tmp_path):
    csv_file = tmp_path / "tickets_sample.csv"
    csv_content = (
        "ticket_id,created_at,category,priority,status,response_time_hrs,resolution_time_hrs,agent_id,customer_rating,issue_summary\n"
        "TKT-001,2024-01-03 09:12,Billing,High,Resolved,0.5,2.3,AGT-04,4.0,Incorrect charge on invoice\n"
        "TKT-002,2024-01-03 11:45,Technical,Critical,Escalated,1.2,,AGT-07,,Login failure after update\n"
        "TKT-003,2024-01-04 08:30,General,Low,Resolved,3.1,5.0,AGT-02,5.0,Request for product docs\n"
        "TKT-004,2024-01-04 14:22,Technical,High,Resolved,0.8,4.7,AGT-04,3.0,API timeout in production\n"
        "TKT-005,2024-01-05 10:05,Billing,Medium,Open,2.0,,AGT-09,,Refund not processed\n"
        "TKT-006,2024-01-05 14:00,Technical,Critical,Resolved,0.4,14.5,AGT-04,2.0,Database connection drop\n"
        "TKT-007,2024-01-06 09:00,Technical,Critical,Open,0.5,,AGT-07,,Server down error\n"
    )
    csv_file.write_text(csv_content)
    
    ds = DataService(csv_path=str(csv_file))
    ds.load_data()
    return AnalyticsService(ds=ds)

def test_query_1_open_tickets(mock_analytics_service):
    # "How many tickets are currently open?"
    res = mock_analytics_service.execute_plan("count", filters={"status": "Open"})
    assert res["value"] == 2

def test_query_2_critical_unresolved_tickets(mock_analytics_service):
    # "How many critical tickets are unresolved?"
    res = mock_analytics_service.execute_plan(
        "count",
        filters={"priority": "Critical", "status": ["Open", "Escalated"]}
    )
    assert res["value"] == 2

def test_query_3_avg_rating_technical(mock_analytics_service):
    # "What is the average customer rating for Technical tickets?"
    res = mock_analytics_service.execute_plan(
        "average",
        metric="customer_rating",
        filters={"category": "Technical"}
    )
    # Ratings for Technical: TKT-004 (3.0), TKT-006 (2.0) -> mean 2.5
    # TKT-002 and TKT-007 are null ratings and MUST be excluded
    assert res["value"] == 2.5
    assert res["record_count"] == 2

def test_query_4_top_agent_resolved(mock_analytics_service):
    # "Which agent resolved the most tickets?"
    res = mock_analytics_service.execute_plan(
        "top_n",
        group_by="agent_id",
        filters={"status": "Resolved"},
        limit=1
    )
    assert len(res["value"]) == 1
    assert res["value"][0]["agent_id"] == "AGT-04"
    assert res["value"][0]["count"] == 3

def test_query_5_critical_not_resolved_within_12_hrs(mock_analytics_service):
    # "Show Critical tickets not resolved within 12 hours."
    res = mock_analytics_service.execute_plan(
        "filter",
        filters={"priority": "Critical", "min_resolution_time_hrs": 12.0}
    )
    # TKT-006 has resolution_time_hrs 14.5
    assert res["record_count"] == 1
    assert res["value"][0]["ticket_id"] == "TKT-006"

def test_query_6_top_categories_by_volume(mock_analytics_service):
    # "What are the top categories by ticket volume?"
    res = mock_analytics_service.execute_plan("group_count", group_by="category")
    # Technical: 4, Billing: 2, General: 1
    val_map = {item["category"]: item["count"] for item in res["value"]}
    assert val_map["Technical"] == 4
    assert val_map["Billing"] == 2
    assert val_map["General"] == 1
