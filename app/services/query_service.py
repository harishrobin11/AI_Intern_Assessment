from typing import Dict, Any, Optional, List
from app.schemas import QueryPlan, QueryResponse
from app.services.llm_service import llm_service, LLMService
from app.services.analytics_service import analytics_service, AnalyticsService
from app.utils.logging_config import logger

SUPPORTED_SCOPE_MESSAGE = (
    "SupportIQ supports natural language queries covering:\n"
    "• Ticket counts (e.g., 'How many open tickets are there?')\n"
    "• Metrics & averages (e.g., 'What is the average customer rating for Technical tickets?')\n"
    "• Agent rankings (e.g., 'Which agent resolved the most tickets?')\n"
    "• High-resolution time or SLA breaches (e.g., 'Show Critical tickets unresolved after 12 hours')\n"
    "• Category & Priority volume breakdowns (e.g., 'What are the top categories by ticket volume?')"
)

class QueryService:
    def __init__(self, llm: Optional[LLMService] = None, analytics: Optional[AnalyticsService] = None):
        self.llm = llm or llm_service
        self.analytics = analytics or analytics_service

    def _format_natural_answer(self, question: str, plan: QueryPlan, result: Dict[str, Any]) -> str:
        op = plan.operation
        val = result.get("value")
        record_count = result.get("record_count", 0)
        filters = plan.filters or {}

        # Build filter description
        filter_parts = []
        for k, v in filters.items():
            if v:
                filter_parts.append(f"{k}='{v}'")
        filter_str = f" ({', '.join(filter_parts)})" if filter_parts else ""

        if op == "count":
            if val == 0:
                return f"No tickets were found matching your criteria{filter_str}."
            elif val == 1:
                return f"There is 1 ticket matching your request{filter_str}."
            else:
                return f"There are {val} tickets matching your request{filter_str}."

        elif op == "average":
            metric_name = plan.metric or "customer_rating"
            metric_label = metric_name.replace("_", " ")
            if val is None or record_count == 0:
                return f"No records found to calculate average {metric_label}{filter_str}."
            return f"The average {metric_label} for {filter_str.strip() or 'matching tickets'} is {val} (based on {record_count} records)."

        elif op == "sum":
            metric_name = plan.metric or "resolution_time_hrs"
            metric_label = metric_name.replace("_", " ")
            return f"The total {metric_label} is {val} hours across {record_count} tickets{filter_str}."

        elif op in ["min", "max"]:
            metric_name = plan.metric or "response_time_hrs"
            metric_label = metric_name.replace("_", " ")
            return f"The {op} {metric_label} is {val} hours{filter_str}."

        elif op == "top_n":
            group_field = plan.group_by or "agent_id"
            if isinstance(val, list) and len(val) > 0:
                top_item = val[0]
                entity = top_item.get(group_field, "Unknown")
                cnt = top_item.get("count", top_item.get(plan.metric or "", ""))
                return f"The top {group_field.replace('_', ' ')} is '{entity}' with {cnt} resolved tickets{filter_str}."
            return f"No top entity data found for {group_field}{filter_str}."

        elif op == "group_count":
            group_field = plan.group_by or "category"
            if isinstance(val, list) and len(val) > 0:
                breakdown = ", ".join([f"{item.get(group_field)}: {item.get('count')}" for item in val[:5]])
                return f"Ticket count by {group_field.replace('_', ' ')}: {breakdown}."
            return f"No group count data found for {group_field}."

        elif op == "group_average":
            group_field = plan.group_by or "category"
            metric_field = plan.metric or "customer_rating"
            if isinstance(val, list) and len(val) > 0:
                breakdown = ", ".join([f"{item.get(group_field)}: {item.get(metric_field)}" for item in val[:5]])
                return f"Average {metric_field.replace('_', ' ')} by {group_field.replace('_', ' ')}: {breakdown}."
            return f"No group average data found."

        elif op in ["filter", "list_records"]:
            returned_count = result.get("returned_count", len(val) if isinstance(val, list) else 0)
            if returned_count == 0:
                return f"No tickets matching your filter criteria{filter_str} were found."
            return f"Found {record_count} ticket(s) matching your request{filter_str}. Showing top {returned_count} records."

        return f"Successfully processed query."

    def process_query(self, question: str) -> QueryResponse:
        logger.info(f"Processing query: '{question}'")
        
        # Step 1: Generate QueryPlan via LLMService
        plan = self.llm.generate_query_plan(question)

        # Handle unsupported or failed planning
        if plan.operation == "unsupported":
            explanation = plan.explanation or "The requested question is outside the supported analytics scope."
            answer = f"{explanation}\n\n{SUPPORTED_SCOPE_MESSAGE}"
            return QueryResponse(
                question=question,
                query_plan=plan,
                result={"value": None, "record_count": 0, "status": "unsupported"},
                answer=answer,
                evidence=[]
            )

        # Step 2: Execute Plan via AnalyticsService
        try:
            result = self.analytics.execute_plan(
                operation=plan.operation,
                metric=plan.metric,
                group_by=plan.group_by,
                filters=plan.filters,
                limit=plan.limit,
                sort_order=plan.sort_order
            )

            # Step 3: Format natural language answer
            answer = self._format_natural_answer(question, plan, result)
            evidence = result.get("evidence", [])

            return QueryResponse(
                question=question,
                query_plan=plan,
                result=result,
                answer=answer,
                evidence=evidence
            )

        except Exception as e:
            logger.error(f"Error executing query plan: {e}")
            fallback_answer = f"Could not execute query plan due to an internal calculation error: {str(e)}"
            return QueryResponse(
                question=question,
                query_plan=plan,
                result={"error": str(e)},
                answer=fallback_answer,
                evidence=[]
            )

# Global singleton instance
query_service = QueryService()
