import json
from dataclasses import dataclass

from google import genai

from ..config import settings

PROCESS_CATEGORIES: dict[str, str] = {
    "철거": "기존 구조물 해체 및 철거 작업",
    "설비": "급수, 배수, 위생, 배관 관련 작업",
    "전기": "전기 배선, 조명, 콘센트, 스위치 작업",
    "타일": "바닥 및 벽면 타일 시공",
    "도장": "벽, 천장, 몰딩 도장 작업",
    "필름": "인테리어 필름, 시트지 시공",
    "바닥": "마루, 장판, 데코타일, LVT 등 바닥재 시공",
    "목공": "몰딩, 걸레받이, 문틀, 목재 구조물 작업",
    "창호": "창문, 문, 샷시 교체 및 시공",
    "주방": "싱크대, 주방 가구 및 상판 시공",
    "욕실": "욕실 리모델링, 위생기기, 도기 시공",
    "가구": "붙박이장, 제작 가구 시공",
    "금속": "금속 구조물, 난간, 프레임 작업",
    "유리": "유리, 거울, 파티션 작업",
    "냉난방": "냉난방기, 환기, 공조 관련 작업",
    "외부공사": "외벽, 외부 바닥, 간판 등 외부 작업",
    "청소": "공사 후 청소, 폐기물 처리",
    "기타": "다른 공정으로 분류되지 않는 항목",
}

CLASSIFICATION_PROMPT = """당신은 인테리어 공사 공정 분류 전문가입니다.
아래 견적 항목을 가장 적합한 공정 카테고리로 분류하세요.

공정 카테고리:
{categories}

분류할 항목:
{items}

응답 형식:
{{
  "classifications": [
    {{
      "item_index": 0,
      "category": "공정카테고리명",
      "confidence": 0.0,
      "reason": "분류 근거"
    }}
  ]
}}

설명 문장 없이 JSON만 반환하세요.
"""

KEYWORD_RULES: list[tuple[str, tuple[str, ...]]] = [
    ("철거", ("철거", "해체", "폐기")),
    ("설비", ("설비", "배관", "급수", "배수", "위생", "수전")),
    ("전기", ("전기", "조명", "배선", "콘센트", "스위치")),
    ("타일", ("타일", "도기질", "자기질", "줄눈")),
    ("도장", ("도장", "페인트", "도색")),
    ("필름", ("필름", "시트")),
    ("바닥", ("마루", "장판", "데코타일", "LVT", "바닥재")),
    ("목공", ("목공", "몰딩", "걸레받이", "문틀", "목재")),
    ("창호", ("창호", "샷시", "창문", "도어", "문짝")),
    ("주방", ("주방", "싱크", "상판")),
    ("욕실", ("욕실", "화장실", "양변기", "세면대")),
    ("가구", ("가구", "붙박이", "수납장")),
    ("금속", ("금속", "스텐", "철재", "난간")),
    ("유리", ("유리", "거울", "파티션")),
    ("냉난방", ("냉난방", "에어컨", "환기", "공조")),
    ("외부공사", ("외부", "외벽", "간판")),
    ("청소", ("청소", "준공청소")),
]


@dataclass
class Classification:
    item_index: int
    category: str
    confidence: float
    reason: str


def classify_items(items: list[dict]) -> list[Classification]:
    if not items:
        return []

    if not settings.gemini_api_key:
        return _keyword_classifications(items)

    categories_text = "\n".join(f"- {k}: {v}" for k, v in PROCESS_CATEGORIES.items())
    items_text = "\n".join(
        f"{i}. {item.get('name', '')} ({item.get('specification', '')})"
        for i, item in enumerate(items)
    )

    client = genai.Client(api_key=settings.gemini_api_key)
    response = client.models.generate_content(
        model="gemini-1.5-flash",
        contents=CLASSIFICATION_PROMPT.format(
            categories=categories_text,
            items=items_text,
        ),
    )

    return _parse_classifications(response.text or "", len(items))


def _parse_classifications(response_text: str, item_count: int) -> list[Classification]:
    start = response_text.find("{")
    end = response_text.rfind("}") + 1
    if start == -1 or end <= start:
        return _fallback_classifications(item_count)

    try:
        data = json.loads(response_text[start:end])
        results = []
        for item in data.get("classifications", []):
            item_index = int(item["item_index"])
            if item_index < 0 or item_index >= item_count:
                continue
            category = item.get("category", "기타")
            if category not in PROCESS_CATEGORIES:
                category = "기타"
            results.append(
                Classification(
                    item_index=item_index,
                    category=category,
                    confidence=float(item.get("confidence", 0.0)),
                    reason=item.get("reason", ""),
                )
            )
        return results or _fallback_classifications(item_count)
    except (json.JSONDecodeError, KeyError, ValueError, TypeError):
        return _fallback_classifications(item_count)


def _keyword_classifications(items: list[dict]) -> list[Classification]:
    results = []
    for i, item in enumerate(items):
        target = f"{item.get('name', '')} {item.get('specification', '')}".lower()
        category = "기타"
        reason = "키워드 매칭 없음"
        confidence = 0.0
        for candidate, keywords in KEYWORD_RULES:
            if any(keyword.lower() in target for keyword in keywords):
                category = candidate
                reason = "로컬 키워드 매칭"
                confidence = 0.35
                break
        results.append(Classification(i, category, confidence, reason))
    return results


def _fallback_classifications(item_count: int) -> list[Classification]:
    return [
        Classification(item_index=i, category="기타", confidence=0.0, reason="")
        for i in range(item_count)
    ]
