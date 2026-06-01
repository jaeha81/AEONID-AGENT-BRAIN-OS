from unittest.mock import patch, MagicMock
from backend.services.process_classifier import classify_items, Classification, PROCESS_CATEGORIES

SAMPLE_ITEMS = [
    {"name": "타일공사", "specification": "300x300 바닥타일"},
    {"name": "전기공사", "specification": "조명 배선"},
    {"name": "도배공사", "specification": "합지 도배"},
]

MOCK_CLASSIFICATION_JSON = """{
  "classifications": [
    {"item_index": 0, "category": "타일", "confidence": 0.97, "reason": "바닥타일 시공"},
    {"item_index": 1, "category": "전기", "confidence": 0.95, "reason": "전기 배선 공사"},
    {"item_index": 2, "category": "도배", "confidence": 0.99, "reason": "합지 도배 시공"}
  ]
}"""

def test_classify_items_returns_classifications():
    mock_response = MagicMock()
    mock_response.text = MOCK_CLASSIFICATION_JSON
    mock_client = MagicMock()
    mock_client.models.generate_content.return_value = mock_response

    with patch("backend.services.process_classifier.genai.Client", return_value=mock_client):
        results = classify_items(SAMPLE_ITEMS)

    assert len(results) == 3
    assert all(isinstance(r, Classification) for r in results)
    assert results[0].category == "타일"
    assert results[0].confidence == 0.97
    assert results[1].category == "전기"

def test_classify_empty_list():
    results = classify_items([])
    assert results == []

def test_process_categories_contains_required_keys():
    required = ["철거", "설비", "전기", "타일", "도배", "페인트", "마루", "목공", "창호", "기타"]
    for cat in required:
        assert cat in PROCESS_CATEGORIES, f"'{cat}' 카테고리가 PROCESS_CATEGORIES에 없습니다"

def test_classify_handles_malformed_json():
    mock_response = MagicMock()
    mock_response.text = "분류할 수 없습니다"
    mock_client = MagicMock()
    mock_client.models.generate_content.return_value = mock_response

    with patch("backend.services.process_classifier.genai.Client", return_value=mock_client):
        results = classify_items(SAMPLE_ITEMS)

    assert len(results) == 3
    assert all(r.category == "기타" for r in results)
    assert all(r.confidence == 0.0 for r in results)
