import json
from dataclasses import dataclass
import anthropic

PROCESS_CATEGORIES: dict[str, str] = {
    "철거": "기존 구조물 해체 및 철거 작업",
    "설비": "급수, 배수, 난방, 배관 관련 작업",
    "전기": "전기 배선, 조명, 콘센트, 스위치 작업",
    "타일": "바닥 및 벽면 타일 시공",
    "도배": "벽지, 도배 시공",
    "페인트": "도색, 도장 작업",
    "마루": "강마루, 원목마루, LVT 등 바닥재 시공",
    "목공": "몰딩, 걸레받이, 문틀, 목재 구조물",
    "창호": "창문, 문, 샷시 교체 및 시공",
    "주방": "싱크대, 주방 가구 및 수납 시공",
    "욕실": "욕실 리모델링, 위생도기, 욕조 시공",
    "가구": "붙박이장, 가구 제작 및 설치",
    "청소": "공사 후 청소, 폐자재 처리",
    "기타": "위 분류에 해당하지 않는 항목"
}

CLASSIFICATION_PROMPT = """당신은 인테리어 공사 공정 분류 전문가입니다.
아래 견적 항목들을 공정 카테고리로 분류하세요.

공정 카테고리:
{categories}

분류할 항목:
{items}

다음 JSON 형식으로만 응답하세요:
{{
  "classifications": [
    {{
      "item_index": 항목인덱스(숫자),
      "category": "공정카테고리명",
      "confidence": 신뢰도(0.0~1.0),
      "reason": "분류근거 한 줄"
    }}
  ]
}}"""

@dataclass
class Classification:
    item_index: int
    category: str
    confidence: float
    reason: str

def classify_items(items: list[dict]) -> list[Classification]:
    if not items:
        return []

    categories_text = "\n".join(f"- {k}: {v}" for k, v in PROCESS_CATEGORIES.items())
    items_text = "\n".join(
        f"{i}. {item.get('name', '')} ({item.get('specification', '')})"
        for i, item in enumerate(items)
    )

    client = anthropic.Anthropic()
    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=2048,
        messages=[{
            "role": "user",
            "content": CLASSIFICATION_PROMPT.format(
                categories=categories_text,
                items=items_text
            )
        }]
    )

    return _parse_classifications(message.content[0].text, len(items))

def _parse_classifications(response_text: str, item_count: int) -> list[Classification]:
    start = response_text.find("{")
    end = response_text.rfind("}") + 1
    if start == -1 or end <= start:
        return _fallback_classifications(item_count)
    try:
        data = json.loads(response_text[start:end])
        return [
            Classification(
                item_index=c["item_index"],
                category=c.get("category", "기타"),
                confidence=float(c.get("confidence", 0.0)),
                reason=c.get("reason", "")
            )
            for c in data.get("classifications", [])
        ]
    except (json.JSONDecodeError, KeyError, ValueError):
        return _fallback_classifications(item_count)

def _fallback_classifications(item_count: int) -> list[Classification]:
    return [
        Classification(item_index=i, category="기타", confidence=0.0, reason="")
        for i in range(item_count)
    ]
