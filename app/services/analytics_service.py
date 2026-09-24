from typing import Dict, Any, List, Optional, Union
import pandas as pd
import numpy as np
from app.services.data_service import data_service, DataService
from app.utils.logging_config import logger

ALLOWED_OPERATIONS = {
    "count", "average", "sum", "min", "max",
    "group_count", "group_average", "top_n",
    "filter", "list_records"
}

ALLOWED_COLUMNS = {
    "ticket_id", "created_at", "category", "priority", "status",
    "response_time_hrs", "resolution_time_hrs", "agent_id",
    "customer_rating", "issue_summary"
}

ALLOWED_FILTER_KEYS = {
    "category", "priority", "status", "agent_id", "ticket_id",
    "customer_rating", "resolution_time_hrs", "response_time_hrs",
    "min_resolution_time_hrs", "max_resolution_time_hrs",
    "min_response_time_hrs", "max_response_time_hrs",
    "min_customer_rating", "max_customer_rating",
    "is_unresolved", "date_from", "date_to", "month"
}

class AnalyticsService:
    def __init__(self, ds: Optional[DataService] = None):
        self.ds = ds or data_service

    def _apply_filters(self, df: pd.DataFrame, filters: Dict[str, Any]) -> pd.DataFrame:
        filtered_df = df.copy()
        if not filters:
            return filtered_df

        for key, val in filters.items():
            if val is None or val == "" or val == []:
                continue

            if key == "category":
                if isinstance(val, list):
                    filtered_df = filtered_df[filtered_df["category"].isin(val)]
                else:
                    filtered_df = filtered_df[filtered_df["category"] == str(val)]

            elif key == "priority":
                if isinstance(val, list):
                    filtered_df = filtered_df[filtered_df["priority"].isin(val)]
                else:
                    filtered_df = filtered_df[filtered_df["priority"] == str(val)]

            elif key == "status":
                if isinstance(val, list):
                    filtered_df = filtered_df[filtered_df["status"].isin(val)]
                else:
                    filtered_df = filtered_df[filtered_df["status"] == str(val)]

            elif key == "agent_id":
                if isinstance(val, list):
                    filtered_df = filtered_df[filtered_df["agent_id"].isin(val)]
                else:
                    filtered_df = filtered_df[filtered_df["agent_id"] == str(val)]

            elif key == "ticket_id":
                if isinstance(val, list):
                    filtered_df = filtered_df[filtered_df["ticket_id"].isin(val)]
                else:
                    filtered_df = filtered_df[filtered_df["ticket_id"] == str(val)]

            elif key == "is_unresolved":
                if bool(val):
                    filtered_df = filtered_df[filtered_df["status"].isin(["Open", "Escalated"])]

            elif key in ["resolution_time_hrs", "min_resolution_time_hrs"]:
                try:
                    num_val = float(val)
                    filtered_df = filtered_df[filtered_df["resolution_time_hrs"] > num_val]
                except (ValueError, TypeError):
                    pass

            elif key == "max_resolution_time_hrs":
                try:
                    num_val = float(val)
                    filtered_df = filtered_df[filtered_df["resolution_time_hrs"] <= num_val]
                except (ValueError, TypeError):
                    pass

            elif key in ["response_time_hrs", "min_response_time_hrs"]:
                try:
                    num_val = float(val)
                    filtered_df = filtered_df[filtered_df["response_time_hrs"] > num_val]
                except (ValueError, TypeError):
                    pass

            elif key == "max_response_time_hrs":
                try:
                    num_val = float(val)
                    filtered_df = filtered_df[filtered_df["response_time_hrs"] <= num_val]
                except (ValueError, TypeError):
                    pass

            elif key in ["customer_rating", "min_customer_rating"]:
                try:
                    num_val = float(val)
                    filtered_df = filtered_df[filtered_df["customer_rating"] >= num_val]
                except (ValueError, TypeError):
                    pass

            elif key == "max_customer_rating":
                try:
                    num_val = float(val)
                    filtered_df = filtered_df[filtered_df["customer_rating"] <= num_val]
                except (ValueError, TypeError):
                    pass

            elif key == "date_from":
                try:
                    dt = pd.to_datetime(val)
                    filtered_df = filtered_df[filtered_df["created_at"] >= dt]
                except Exception:
                    pass

            elif key == "date_to":
                try:
                    dt = pd.to_datetime(val)
                    filtered_df = filtered_df[filtered_df["created_at"] <= dt]
                except Exception:
                    pass

            elif key == "month":
                try:
                    if isinstance(val, int):
                        filtered_df = filtered_df[filtered_df["created_at"].dt.month == val]
                    elif isinstance(val, str) and val.isdigit():
                        filtered_df = filtered_df[filtered_df["created_at"].dt.month == int(val)]
                except Exception:
                    pass

        return filtered_df

    def _format_records(self, df: pd.DataFrame, limit: int = 20) -> List[Dict[str, Any]]:
        records = []
        subset = df.head(limit)
        for _, row in subset.iterrows():
            rec = {
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
            }
            records.append(rec)
        return records

    def execute_plan(
        self,
        operation: str,
        metric: Optional[str] = None,
        group_by: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 20,
        sort_order: str = "desc"
    ) -> Dict[str, Any]:
        filters = filters or {}
        df = self.ds.get_df()

        if operation not in ALLOWED_OPERATIONS:
            raise ValueError(f"Unsupported analytics operation: '{operation}'")

        filtered_df = self._apply_filters(df, filters)
        total_matching = len(filtered_df)

        if operation == "count":
            return {
                "operation": "count",
                "filters": filters,
                "value": total_matching,
                "record_count": total_matching,
                "evidence": self._format_records(filtered_df, limit=limit)
            }

        elif operation in ["average", "mean"]:
            metric = metric or "customer_rating"
            if metric not in ALLOWED_COLUMNS:
                raise ValueError(f"Invalid metric column: '{metric}'")
            
            s = filtered_df[metric].dropna()
            avg_val = round(float(s.mean()), 2) if len(s) > 0 else 0.0
            
            return {
                "operation": "average",
                "metric": metric,
                "filters": filters,
                "value": avg_val,
                "record_count": len(s),
                "total_matching": total_matching,
                "evidence": self._format_records(filtered_df, limit=limit)
            }

        elif operation == "sum":
            metric = metric or "resolution_time_hrs"
            if metric not in ALLOWED_COLUMNS:
                raise ValueError(f"Invalid metric column: '{metric}'")

            s = filtered_df[metric].dropna()
            sum_val = round(float(s.sum()), 2) if len(s) > 0 else 0.0

            return {
                "operation": "sum",
                "metric": metric,
                "filters": filters,
                "value": sum_val,
                "record_count": len(s),
                "total_matching": total_matching,
                "evidence": self._format_records(filtered_df, limit=limit)
            }

        elif operation == "min":
            metric = metric or "response_time_hrs"
            if metric not in ALLOWED_COLUMNS:
                raise ValueError(f"Invalid metric column: '{metric}'")

            s = filtered_df[metric].dropna()
            min_val = round(float(s.min()), 2) if len(s) > 0 else 0.0

            return {
                "operation": "min",
                "metric": metric,
                "filters": filters,
                "value": min_val,
                "record_count": len(s),
                "total_matching": total_matching,
                "evidence": self._format_records(filtered_df.sort_values(metric, ascending=True), limit=limit)
            }

        elif operation == "max":
            metric = metric or "resolution_time_hrs"
            if metric not in ALLOWED_COLUMNS:
                raise ValueError(f"Invalid metric column: '{metric}'")

            s = filtered_df[metric].dropna()
            max_val = round(float(s.max()), 2) if len(s) > 0 else 0.0

            return {
                "operation": "max",
                "metric": metric,
                "filters": filters,
                "value": max_val,
                "record_count": len(s),
                "total_matching": total_matching,
                "evidence": self._format_records(filtered_df.sort_values(metric, ascending=False), limit=limit)
            }

        elif operation == "group_count":
            group_by = group_by or "category"
            if group_by not in ALLOWED_COLUMNS:
                raise ValueError(f"Invalid group_by column: '{group_by}'")

            grouped = filtered_df.groupby(group_by).size().reset_index(name="count")
            ascending = (sort_order.lower() == "asc")
            grouped = grouped.sort_values("count", ascending=ascending)
            results = grouped.to_dict(orient="records")

            return {
                "operation": "group_count",
                "group_by": group_by,
                "filters": filters,
                "value": results,
                "record_count": total_matching,
                "evidence": self._format_records(filtered_df, limit=limit)
            }

        elif operation == "group_average":
            group_by = group_by or "category"
            metric = metric or "customer_rating"
            if group_by not in ALLOWED_COLUMNS or metric not in ALLOWED_COLUMNS:
                raise ValueError(f"Invalid group_by '{group_by}' or metric '{metric}'")

            grouped = filtered_df.groupby(group_by)[metric].mean().reset_index()
            grouped[metric] = grouped[metric].round(2)
            ascending = (sort_order.lower() == "asc")
            grouped = grouped.sort_values(metric, ascending=ascending)
            results = grouped.to_dict(orient="records")

            return {
                "operation": "group_average",
                "group_by": group_by,
                "metric": metric,
                "filters": filters,
                "value": results,
                "record_count": total_matching,
                "evidence": self._format_records(filtered_df, limit=limit)
            }

        elif operation == "top_n":
            group_by = group_by or "agent_id"
            metric = metric or "ticket_count"
            ascending = (sort_order.lower() == "asc")

            if metric == "ticket_count" or metric is None:
                counts = filtered_df.groupby(group_by).size().reset_index(name="count")
                counts = counts.sort_values("count", ascending=ascending).head(limit)
                results = counts.to_dict(orient="records")
            else:
                grouped = filtered_df.groupby(group_by)[metric].mean().reset_index()
                grouped[metric] = grouped[metric].round(2)
                grouped = grouped.sort_values(metric, ascending=ascending).head(limit)
                results = grouped.to_dict(orient="records")

            return {
                "operation": "top_n",
                "group_by": group_by,
                "metric": metric,
                "filters": filters,
                "limit": limit,
                "value": results,
                "record_count": total_matching,
                "evidence": self._format_records(filtered_df, limit=limit)
            }

        elif operation in ["filter", "list_records"]:
            sort_col = metric if (metric and metric in ALLOWED_COLUMNS) else "created_at"
            ascending = (sort_order.lower() == "asc")
            
            if sort_col in filtered_df.columns:
                sorted_df = filtered_df.sort_values(sort_col, ascending=ascending, na_position="last")
            else:
                sorted_df = filtered_df

            records = self._format_records(sorted_df, limit=limit)

            return {
                "operation": operation,
                "filters": filters,
                "value": records,
                "record_count": total_matching,
                "returned_count": len(records),
                "evidence": records
            }

        raise ValueError(f"Operation '{operation}' is not supported.")

# Global singleton instance
analytics_service = AnalyticsService()
