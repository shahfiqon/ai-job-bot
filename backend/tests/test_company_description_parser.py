import json

from app.utils.company_description_parser import (
    CompanyDescriptionInsights,
    parse_company_description,
)


class _DummyResponse:
    def __init__(self, payload: str):
        self.response = payload


class _DummyClient:
    def __init__(self, payload: str, *, should_raise: bool = False):
        self.payload = payload
        self.should_raise = should_raise

    def generate(self, **_: object) -> _DummyResponse:
        if self.should_raise:
            raise RuntimeError("simulated Ollama failure")
        return _DummyResponse(self.payload)


def test_llm_response_is_parsed_successfully():
    description = (
        "Acme Labs builds a proprietary SaaS platform that helps developers ship faster."
    )
    payload = json.dumps(
        {
            "has_own_products": True,
            "is_recruiting_company": False,
        }
    )

    result = parse_company_description(description, client=_DummyClient(payload))

    assert result == CompanyDescriptionInsights(
        has_own_products=True,
        is_recruiting_company=False,
    )


def test_invalid_llm_output_falls_back_to_heuristics():
    description = (
        "BrightBridge is a staffing and recruitment agency specializing in executive search."
    )
    invalid_payload = "not-json"

    result = parse_company_description(description, client=_DummyClient(invalid_payload))

    assert result.has_own_products is False
    assert result.is_recruiting_company is True
