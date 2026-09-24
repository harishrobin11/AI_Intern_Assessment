import json
import pytest
from unittest.mock import MagicMock
from groq import RateLimitError
from app.schemas import QueryPlan
from app.services.llm_service import LLMService

def test_missing_api_key():
    service = LLMService(client=None)
    service.api_key = ""
    plan = service.generate_query_plan("How many open tickets?")
    assert plan.operation == "unsupported"
    assert "Groq API Key is not configured" in plan.explanation

def test_valid_llm_query_plan_generation():
    mock_client = MagicMock()
    mock_choice = MagicMock()
    mock_choice.message.content = json.dumps({
        "operation": "count",
        "metric": None,
        "group_by": None,
        "filters": {"priority": "Critical", "is_unresolved": True},
        "limit": 20,
        "explanation": "Count unresolved critical tickets"
    })
    mock_client.chat.completions.create.return_value.choices = [mock_choice]

    service = LLMService(client=mock_client)
    service.api_key = "mock_key"

    plan = service.generate_query_plan("How many critical tickets are unresolved?")
    assert isinstance(plan, QueryPlan)
    assert plan.operation == "count"
    assert plan.filters["priority"] == "Critical"
    assert plan.filters["is_unresolved"] is True
    assert plan.explanation == "Count unresolved critical tickets"

def test_llm_invalid_json_handling():
    mock_client = MagicMock()
    mock_choice = MagicMock()
    mock_choice.message.content = "Not valid JSON response at all"
    mock_client.chat.completions.create.return_value.choices = [mock_choice]

    service = LLMService(client=mock_client)
    service.api_key = "mock_key"

    plan = service.generate_query_plan("Invalid JSON query")
    assert plan.operation == "unsupported"
    assert "invalid JSON" in plan.explanation

def test_llm_rate_limit_handling():
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.status_code = 429
    mock_client.chat.completions.create.side_effect = RateLimitError(
        message="Rate limit exceeded",
        response=mock_response,
        body=None
    )

    service = LLMService(client=mock_client)
    service.api_key = "mock_key"

    plan = service.generate_query_plan("High volume query")
    assert plan.operation == "unsupported"
    assert "rate limit exceeded" in plan.explanation.lower()
