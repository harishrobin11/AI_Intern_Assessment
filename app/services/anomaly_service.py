from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np
from app.schemas import Anomaly, AnomalyResponse
from app.services.data_service import data_service, DataService
from app.utils.logging_config import logger

class AnomalyService:
    def __init__(
        self,
        ds: Optional[DataService] = None,
        aging_hours_threshold: float = 24.0,
        low_rating_threshold: float = 2.0,
        slow_response_threshold_hrs: float = 4.0
    ):
        self.ds = ds or data_service
        self.aging_hours_threshold = aging_hours_threshold
        self.low_rating_threshold = low_rating_threshold
        self.slow_response_threshold_hrs = slow_response_threshold_hrs

    def detect_anomalies(
        self,
        anomaly_type_filter: Optional[str] = None,
        severity_filter: Optional[str] = None
    ) -> AnomalyResponse:
        df = self.ds.get_df().copy()
        if len(df) == 0:
            return AnomalyResponse(total_anomalies=0, anomalies=[])

        anomalies: List[Anomaly] = []

        # Reference max date in dataset for deterministic relative age calculation
        max_date = df["created_at"].max()

        # Rule 1: Critical unresolved tickets
        crit_unresolved = df[(df["priority"] == "Critical") & (df["status"].isin(["Open", "Escalated"]))]
        for _, row in crit_unresolved.iterrows():
            anomalies.append(Anomaly(
                ticket_id=str(row["ticket_id"]),
                anomaly_type="critical_unresolved",
                severity="critical",
                reason="Critical ticket remains unresolved and open",
                detected_value=str(row["status"]),
                threshold="status in ['Open', 'Escalated']"
            ))

        # Rule 2: High/Critical unresolved tickets older than aging_hours_threshold
        if pd.notna(max_date):
            unresolved = df[df["status"].isin(["Open", "Escalated"]) & df["priority"].isin(["High", "Critical"])]
            for _, row in unresolved.iterrows():
                if pd.notna(row["created_at"]):
                    age_hrs = (max_date - row["created_at"]).total_seconds() / 3600.0
                    if age_hrs > self.aging_hours_threshold:
                        # Avoid duplicating if already added as critical_unresolved
                        if not any(a.ticket_id == str(row["ticket_id"]) and a.anomaly_type == "aging_unresolved" for a in anomalies):
                            anomalies.append(Anomaly(
                                ticket_id=str(row["ticket_id"]),
                                anomaly_type="aging_unresolved",
                                severity="high",
                                reason=f"{row['priority']} priority ticket unresolved for {round(age_hrs, 1)} hours (exceeds {self.aging_hours_threshold}h threshold)",
                                detected_value=round(age_hrs, 1),
                                threshold=self.aging_hours_threshold
                            ))

        # Rule 3: Resolution time IQR outliers (only for resolved tickets with non-null resolution_time_hrs)
        resolved_df = df[df["status"] == "Resolved"].dropna(subset=["resolution_time_hrs"])
        if len(resolved_df) >= 4:
            q1 = resolved_df["resolution_time_hrs"].quantile(0.25)
            q3 = resolved_df["resolution_time_hrs"].quantile(0.75)
            iqr = q3 - q1
            upper_bound = round(float(q3 + 1.5 * iqr), 2)

            outliers = resolved_df[resolved_df["resolution_time_hrs"] > upper_bound]
            for _, row in outliers.iterrows():
                val = round(float(row["resolution_time_hrs"]), 2)
                anomalies.append(Anomaly(
                    ticket_id=str(row["ticket_id"]),
                    anomaly_type="resolution_time_outlier",
                    severity="medium",
                    reason=f"Resolution time of {val} hrs exceeds upper statistical bound of {upper_bound} hrs (Q3 + 1.5*IQR)",
                    detected_value=val,
                    threshold=upper_bound
                ))

        # Rule 4: Low customer rating (resolved tickets with rating <= 2)
        low_rated = df[df["status"] == "Resolved"].dropna(subset=["customer_rating"])
        low_rated = low_rated[low_rated["customer_rating"] <= self.low_rating_threshold]
        for _, row in low_rated.iterrows():
            val = float(row["customer_rating"])
            anomalies.append(Anomaly(
                ticket_id=str(row["ticket_id"]),
                anomaly_type="low_customer_rating",
                severity="medium",
                reason=f"Customer rating of {val} is at or below rating threshold ({self.low_rating_threshold})",
                detected_value=val,
                threshold=self.low_rating_threshold
            ))

        # Rule 5: Slow response time
        slow_resp = df.dropna(subset=["response_time_hrs"])
        slow_resp = slow_resp[slow_resp["response_time_hrs"] > self.slow_response_threshold_hrs]
        for _, row in slow_resp.iterrows():
            val = round(float(row["response_time_hrs"]), 2)
            anomalies.append(Anomaly(
                ticket_id=str(row["ticket_id"]),
                anomaly_type="slow_first_response",
                severity="low",
                reason=f"First response time of {val} hrs exceeds response SLA threshold ({self.slow_response_threshold_hrs} hrs)",
                detected_value=val,
                threshold=self.slow_response_threshold_hrs
            ))

        # Apply filters if provided
        filtered_anomalies = anomalies
        if anomaly_type_filter:
            filtered_anomalies = [a for a in filtered_anomalies if a.anomaly_type == anomaly_type_filter]

        if severity_filter:
            filtered_anomalies = [a for a in filtered_anomalies if a.severity == severity_filter.lower()]

        return AnomalyResponse(
            total_anomalies=len(filtered_anomalies),
            anomalies=filtered_anomalies
        )

# Global singleton instance
anomaly_service = AnomalyService()
