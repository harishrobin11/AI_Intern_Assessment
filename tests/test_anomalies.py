import pytest
import pandas as pd
from app.services.data_service import DataService
from app.services.anomaly_service import AnomalyService

@pytest.fixture
def mock_anomaly_service(tmp_path):
    csv_file = tmp_path / "tickets_anomalies_sample.csv"
    csv_content = (
        "ticket_id,created_at,category,priority,status,response_time_hrs,resolution_time_hrs,agent_id,customer_rating,issue_summary\n"
        "TKT-001,2024-01-01 09:00,Billing,Low,Resolved,0.5,2.0,AGT-01,5.0,Normal ticket 1\n"
        "TKT-002,2024-01-01 10:00,Billing,Low,Resolved,0.5,2.5,AGT-01,4.0,Normal ticket 2\n"
        "TKT-003,2024-01-01 11:00,General,Low,Resolved,0.5,2.2,AGT-02,4.0,Normal ticket 3\n"
        "TKT-004,2024-01-01 12:00,General,Low,Resolved,0.5,2.8,AGT-02,5.0,Normal ticket 4\n"
        "TKT-005,2024-01-01 13:00,Technical,High,Resolved,0.5,25.0,AGT-03,1.0,IQR outlier & low rating\n"
        "TKT-006,2024-01-01 14:00,Technical,Critical,Escalated,5.0,,AGT-04,,Critical unresolved & slow resp\n"
        "TKT-007,2024-01-05 15:00,Billing,High,Open,0.5,,AGT-05,,Recent open ticket\n"
    )
    csv_file.write_text(csv_content)

    ds = DataService(csv_path=str(csv_file))
    ds.load_data()
    return AnomalyService(ds=ds)

def test_detect_critical_unresolved(mock_anomaly_service):
    res = mock_anomaly_service.detect_anomalies(anomaly_type_filter="critical_unresolved")
    assert res.total_anomalies == 1
    assert res.anomalies[0].ticket_id == "TKT-006"
    assert res.anomalies[0].severity == "critical"

def test_detect_iqr_resolution_outlier(mock_anomaly_service):
    res = mock_anomaly_service.detect_anomalies(anomaly_type_filter="resolution_time_outlier")
    # TKT-005 has 25.0 hrs, while normal are 2.0 - 2.8 hrs
    # TKT-006 & TKT-007 have null resolution time and MUST NOT be flagged as resolution outliers!
    assert res.total_anomalies == 1
    assert res.anomalies[0].ticket_id == "TKT-005"
    assert res.anomalies[0].detected_value == 25.0

def test_detect_low_customer_rating(mock_anomaly_service):
    res = mock_anomaly_service.detect_anomalies(anomaly_type_filter="low_customer_rating")
    assert res.total_anomalies == 1
    assert res.anomalies[0].ticket_id == "TKT-005"
    assert res.anomalies[0].detected_value == 1.0

def test_detect_slow_response(mock_anomaly_service):
    res = mock_anomaly_service.detect_anomalies(anomaly_type_filter="slow_first_response")
    # TKT-006 has response_time_hrs = 5.0 (exceeds default threshold 4.0)
    assert res.total_anomalies == 1
    assert res.anomalies[0].ticket_id == "TKT-006"

def test_severity_filter(mock_anomaly_service):
    res_critical = mock_anomaly_service.detect_anomalies(severity_filter="critical")
    assert all(a.severity == "critical" for a in res_critical.anomalies)

def test_null_resolution_time_handling(mock_anomaly_service):
    # Ensure unresolved tickets with null resolution time are not flagged as resolution outliers
    res = mock_anomaly_service.detect_anomalies(anomaly_type_filter="resolution_time_outlier")
    ticket_ids = [a.ticket_id for a in res.anomalies]
    assert "TKT-006" not in ticket_ids
    assert "TKT-007" not in ticket_ids
