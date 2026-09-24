import json
from typing import Dict, Any, Optional
from groq import Groq, APIError, RateLimitError
from app.config import settings
from app.schemas import QueryPlan
from app.utils.logging_config import logger

SYSTEM_PROMPT = """You are a query-planning assistant for a customer support analytics dataset.
Your sole job is to convert a user's natural-language question into ONE valid JSON query plan.

CRITICAL RULES:
1. Do NOT calculate values, averages, or totals.
2. Do NOT write Python, SQL, or executable code.
3. Do NOT invent fields, operations, or filter values.
4. Output raw valid JSON ONLY. No markdown formatting, no code blocks (do NOT use ```json).

DATASET FIELDS:
- ticket_id (string)
- created_at (datetime)
- category (string: "Billing", "Technical", "General")
- priority (string: "Low", "Medium", "High", "Critical")
- status (string: "Open", "Resolved", "Escalated")
- response_time_hrs (float)
- resolution_time_hrs (float, null if unresolved)
- agent_id (string, e.g., "AGT-01", "AGT-04")
- customer_rating (float 1-5, null if unresolved)
- issue_summary (string)

ALLOWED OPERATIONS:
- count (count matching tickets)
- average (mean of a numeric metric)
- sum (sum of a numeric metric)
- min (minimum of a numeric metric)
- max (maximum of a numeric metric)
- group_count (group by a field and count tickets)
- group_average (group by a field and average a metric)
- top_n (top entities ranked by count or metric)
- filter / list_records (list matching ticket records)
- unsupported (if question cannot be answered from dataset)

ALLOWED METRICS:
customer_rating, response_time_hrs, resolution_time_hrs

ALLOWED GROUP_BY FIELDS:
category, priority, status, agent_id

ALLOWED FILTER KEYS:
category, priority, status, agent_id, min_resolution_time_hrs, max_resolution_time_hrs, min_response_time_hrs, max_response_time_hrs, min_customer_rating, max_customer_rating, is_unresolved, month

JSON SCHEMA TO RETURN:
{
  "operation": "count" | "average" | "sum" | "min" | "max" | "group_count" | "group_average" | "top_n" | "filter" | "list_records" | "unsupported",
  "metric": string | null,
  "group_by": string | null,
  "filters": {
    "category": string or string[],
    "priority": string or string[],
    "status": string or string[],
    "agent_id": string or string[],
    "min_resolution_time_hrs": number,
    "max_resolution_time_hrs": number,
    "min_response_time_hrs": number,
    "max_response_time_hrs": number,
    "min_customer_rating": number,
    "max_customer_rating": number,
    "is_unresolved": boolean,
    "month": number (1-12)
  },
  "limit": number (1-100),
  "explanation": string
}

EXAMPLES:
User: "How many critical tickets are unresolved?"
JSON:
{
  "operation": "count",
  "metric": null,
  "group_by": null,
  "filters": {"priority": "Critical", "is_unresolved": true},
  "limit": 20,
  "explanation": "Count unresolved tickets with Critical priority"
}

User: "What is the average customer rating for Technical tickets?"
JSON:
{
  "operation": "average",
  "metric": "customer_rating",
  "group_by": null,
  "filters": {"category": "Technical"},
  "limit": 20,
  "explanation": "Calculate average customer_rating for Technical category"
}

User: "Which agent resolved the most tickets?"
JSON:
{
  "operation": "top_n",
  "metric": "ticket_count",
  "group_by": "agent_id",
  "filters": {"status": "Resolved"},
  "limit": 1,
  "explanation": "Find agent with the highest count of resolved tickets"
}
"""

class LLMService:
    def __init__(self, client: Optional[Groq] = None, model: Optional[str] = None):
        self.api_key = settings.GROQ_API_KEY
        self.model = model or settings.GROQ_MODEL
        self._client = client

    @property
    def client(self) -> Optional[Groq]:
        if self._client is None and self.api_key:
            try:
                self._client = Groq(api_key=self.api_key)
            except Exception as e:
                logger.error(f"Failed to initialize Groq client: {e}")
                self._client = None
        return self._client

    def generate_query_plan(self, question: str) -> QueryPlan:
        if not self.api_key or self.api_key.startswith("replace_with"):
            logger.warning("Groq API Key missing or default.")
            return QueryPlan(
                operation="unsupported",
                explanation="Groq API Key is not configured. Please add GROQ_API_KEY to your .env file."
            )

        cli = self.client
        if not cli:
            return QueryPlan(
                operation="unsupported",
                explanation="Groq client unavailable. Please check server logs and configuration."
            )

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Question: {question}"}
        ]

        try:
            logger.info(f"Sending prompt to Groq model {self.model} for question: '{question}'")
            response = cli.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.0,
                max_tokens=500
            )

            raw_text = response.choices[0].message.content.strip()
            logger.debug(f"Raw Groq response text: {raw_text}")

            # Strip Markdown triple backticks if present
            if raw_text.startswith("```"):
                lines = raw_text.splitlines()
                if lines[0].startswith("```"):
                    lines = lines[1:]
                if lines and lines[-1].startswith("```"):
                    lines = lines[:-1]
                raw_text = "\n".join(lines).strip()

            data = json.loads(raw_text)
            plan = QueryPlan(**data)
            return plan

        except RateLimitError as rle:
            logger.error(f"Groq RateLimitError: {rle}")
            return QueryPlan(
                operation="unsupported",
                explanation="Groq API rate limit exceeded. Please wait a moment and try again."
            )

        except APIError as apie:
            logger.error(f"Groq API Error: {apie}")
            return QueryPlan(
                operation="unsupported",
                explanation=f"Groq API error: {apie.message if hasattr(apie, 'message') else str(apie)}"
            )

        except json.JSONDecodeError as jde:
            logger.error(f"Failed to parse LLM response as JSON: {jde}")
            return QueryPlan(
                operation="unsupported",
                explanation="Model generated invalid JSON output. Please rephrase your question."
            )

        except Exception as e:
            logger.error(f"Unexpected error in LLM query planning: {e}")
            return QueryPlan(
                operation="unsupported",
                explanation=f"Query planning error: {str(e)}"
            )

# Global singleton instance
llm_service = LLMService()
