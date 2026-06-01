import pytest
from unittest.mock import patch, MagicMock
from backend.services.ai_extractor import extract_items, ExtractedEstimate

SAMPLE_RAW = {
    "text": """현장명: 강남구 역삼동 000호
항목명  규격  수량  단위  단가  합계
타일공사  300x300  100  장  5000  500000
도배공사  합지  1  식  800000  800000
전기공사  조명포함  1  식  1200000  1200000
""",
    "tables": [[
        ["항목명", "규격", "수량", "단위", "단가", "합계"],
        ["타일공사", "300x300", "100", "장", "5000", "500000"],
        ["도배공사", "합지", "1", "식", "800000", "800000"],
    ]]
}

MOCK_RESPONSE_JSON = """{
  "items": [
    {"name": "타일공사", "specification": "300x300", "quantity": 100, "unit": "장", "unit_price": 5000, "total_price": 500000, "notes": ""},
    {"name": "도배공사", "specification": "합지", "quantity": 1, "unit": "식", "unit_price": 800000, "total_price": 800000, "notes": ""},
    {"name": "전기공사", "specification": "조명포함", "quantity": 1, "unit": "식", "unit_price": 1200000, "total_price": 1200000, "notes": ""}
  ],
  "site_name": "강남구 역삼동 000호",
  "total_amount": 2500000
}"""

def test_extract_items_returns_extracted_estimate(monkeypatch):
    mock_content = MagicMock()
    mock_content.text = MOCK_RESPONSE_JSON
    mock_msg = MagicMock()
    mock_msg.content = [mock_content]

    mock_client = MagicMock()
    mock_client.messages.create.return_value = mock_msg

    with patch("backend.services.ai_extractor.anthropic.Anthropic", return_value=mock_client):
        result = extract_items(SAMPLE_RAW)

    assert isinstance(result, ExtractedEstimate)
    assert len(result.items) == 3
    assert result.items[0]["name"] == "타일공사"
    assert result.total_amount == 2500000
    assert result.site_name == "강남구 역삼동 000호"

def test_extract_items_handles_malformed_json(monkeypatch):
    mock_content = MagicMock()
    mock_content.text = "죄송합니다, 견적서를 분석할 수 없습니다."
    mock_msg = MagicMock()
    mock_msg.content = [mock_content]

    mock_client = MagicMock()
    mock_client.messages.create.return_value = mock_msg

    with patch("backend.services.ai_extractor.anthropic.Anthropic", return_value=mock_client):
        result = extract_items({"text": "not a real estimate", "tables": []})

    assert isinstance(result, ExtractedEstimate)
    assert result.items == []
    assert result.total_amount == 0
