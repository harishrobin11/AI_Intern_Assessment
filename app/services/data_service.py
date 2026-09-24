import os
from typing import Dict, Any, List, Optional
import pandas as pd
from datetime import datetime
from app.config import settings
from app.utils.logging_config import logger

REQUIRED_COLUMNS = [
    "ticket_id", "created_at", "category", "priority", "status",
    "response_time_hrs", "resolution_time_hrs", "agent_id",
    "customer_rating", "issue_summary"
]

ALLOWED_CATEGORIES = {"Billing", "Technical", "General"}
ALLOWED_PRIORITIES = {"Low", "Medium", "High", "Critical"}
ALLOWED_STATUSES = {"Open", "Resolved", "Escalated"}

class DataService:
    def __init__(self, csv_path: Optional[str] = None):
        self.csv_path = csv_path or settings.DATA_PATH
        self._df: Optional[pd.DataFrame] = None
        self._loaded_at: Optional[datetime] = None

    def load_data(self, force_reload: bool = False) -> pd.DataFrame:
        if self._df is not None and not force_reload:
            return self._df

        if not os.path.exists(self.csv_path):
            logger.error(f"Dataset file not found at path: {self.csv_path}")
            raise FileNotFoundError(
                f"SupportIQ Dataset missing! Could not find file at '{self.csv_path}'. "
                "Please verify the DATA_PATH setting or place support_tickets.csv in the data directory."
            )

        try:
            df = pd.read_csv(self.csv_path)
        except Exception as e:
            logger.error(f"Failed to read CSV at {self.csv_path}: {e}")
            raise ValueError(f"Failed to read malformed CSV dataset: {str(e)}")

        missing = set(REQUIRED_COLUMNS) - set(df.columns)
        if missing:
            logger.error(f"Missing required columns in dataset: {sorted(missing)}")
            raise ValueError(f"Invalid dataset schema. Missing required columns: {sorted(missing)}")

        # Convert created_at to datetime
        df["created_at"] = pd.to_datetime(df["created_at"], errors="coerce")

        # Coerce numeric columns safely
        df["response_time_hrs"] = pd.to_numeric(df["response_time_hrs"], errors="coerce")
        df["resolution_time_hrs"] = pd.to_numeric(df["resolution_time_hrs"], errors="coerce")
        df["customer_rating"] = pd.to_numeric(df["customer_rating"], errors="coerce")

        # Clean string columns
        for col in ["ticket_id", "category", "priority", "status", "agent_id", "issue_summary"]:
            df[col] = df[col].astype(str).str.strip()

        self._df = df
        self._loaded_at = datetime.now()
        logger.info(f"Successfully loaded {len(df)} support ticket records from {self.csv_path}")
        return self._df

    def get_df(self) -> pd.DataFrame:
        if self._df is None:
            return self.load_data()
        return self._df

    def get_health_status(self) -> Dict[str, Any]:
        exists = os.path.exists(self.csv_path)
        is_loaded = self._df is not None
        row_count = len(self._df) if is_loaded else 0

        return {
            "dataset_path": self.csv_path,
            "file_exists": exists,
            "is_loaded": is_loaded,
            "row_count": row_count,
            "loaded_at": self._loaded_at.isoformat() if self._loaded_at else None,
            "status": "healthy" if (exists and is_loaded and row_count > 0) else "unhealthy"
        }

    def get_summary_stats(self) -> Dict[str, Any]:
        df = self.get_df()
        
        total_tickets = len(df)
        status_counts = df["status"].value_counts().to_dict()
        priority_counts = df["priority"].value_counts().to_dict()
        category_counts = df["category"].value_counts().to_dict()

        avg_resp = df["response_time_hrs"].mean()
        avg_resol = df["resolution_time_hrs"].dropna().mean()
        avg_rating = df["customer_rating"].dropna().mean()

        unresolved_count = df[df["status"].isin(["Open", "Escalated"])].shape[0]
        critical_unresolved_count = df[(df["priority"] == "Critical") & (df["status"].isin(["Open", "Escalated"]))].shape[0]

        return {
            "total_tickets": total_tickets,
            "unresolved_tickets": unresolved_count,
            "critical_unresolved_tickets": critical_unresolved_count,
            "status_counts": status_counts,
            "priority_counts": priority_counts,
            "category_counts": category_counts,
            "avg_response_time_hrs": round(float(avg_resp), 2) if pd.notna(avg_resp) else None,
            "avg_resolution_time_hrs": round(float(avg_resol), 2) if pd.notna(avg_resol) else None,
            "avg_customer_rating": round(float(avg_rating), 2) if pd.notna(avg_rating) else None
        }

# Global singleton instance
data_service = DataService()
