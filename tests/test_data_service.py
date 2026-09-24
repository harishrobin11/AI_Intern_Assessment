import os
import pytest
import pandas as pd
from app.services.data_service import DataService, REQUIRED_COLUMNS

def test_missing_csv_file(tmp_path):
    non_existent_file = str(tmp_path / "non_existent.csv")
    service = DataService(csv_path=non_existent_file)
    
    with pytest.raises(FileNotFoundError) as exc_info:
        service.load_data()
    assert "SupportIQ Dataset missing" in str(exc_info.value)

def test_malformed_csv_missing_columns(tmp_path):
    bad_csv = tmp_path / "bad_tickets.csv"
    bad_csv.write_text("ticket_id,created_at,category\nTKT-001,2024-01-01,Billing\n")
    
    service = DataService(csv_path=str(bad_csv))
    with pytest.raises(ValueError) as exc_info:
        service.load_data()
    assert "Missing required columns" in str(exc_info.value)

def test_valid_csv_loading(tmp_path):
    valid_csv = tmp_path / "valid_tickets.csv"
    content = (
        "ticket_id,created_at,category,priority,status,response_time_hrs,resolution_time_hrs,agent_id,customer_rating,issue_summary\n"
        "TKT-001,2024-01-03 09:12,Billing,High,Resolved,0.5,2.3,AGT-04,4,Incorrect charge on invoice\n"
        "TKT-002,2024-01-03 11:45,Technical,Critical,Open,1.2,,AGT-07,,Login failure after update\n"
    )
    valid_csv.write_text(content)
    
    service = DataService(csv_path=str(valid_csv))
    df = service.load_data()
    
    assert len(df) == 2
    assert pd.api.types.is_datetime64_any_dtype(df["created_at"])
    # Check null preservation for unresolved ticket (TKT-002)
    assert pd.isna(df.loc[df["ticket_id"] == "TKT-002", "resolution_time_hrs"].values[0])
    assert pd.isna(df.loc[df["ticket_id"] == "TKT-002", "customer_rating"].values[0])
    # Check resolved ticket values (TKT-001)
    assert df.loc[df["ticket_id"] == "TKT-001", "resolution_time_hrs"].values[0] == 2.3
    assert df.loc[df["ticket_id"] == "TKT-001", "customer_rating"].values[0] == 4.0

def test_health_status_and_summary_stats(tmp_path):
    valid_csv = tmp_path / "valid_tickets.csv"
    content = (
        "ticket_id,created_at,category,priority,status,response_time_hrs,resolution_time_hrs,agent_id,customer_rating,issue_summary\n"
        "TKT-001,2024-01-03 09:12,Billing,High,Resolved,1.0,2.0,AGT-01,4,Billing issue\n"
        "TKT-002,2024-01-03 11:45,Technical,Critical,Open,2.0,,AGT-02,,Tech issue\n"
    )
    valid_csv.write_text(content)
    
    service = DataService(csv_path=str(valid_csv))
    service.load_data()
    
    health = service.get_health_status()
    assert health["status"] == "healthy"
    assert health["row_count"] == 2
    
    summary = service.get_summary_stats()
    assert summary["total_tickets"] == 2
    assert summary["unresolved_tickets"] == 1
    assert summary["critical_unresolved_tickets"] == 1
    assert summary["avg_customer_rating"] == 4.0
