import json
from dataclasses import dataclass, field

from google import genai

from ..config import settings

EXTRACTION_PROMPT = """당신은 인테리어 공사 견적서를 분석하는 전문가입니다.
아래 견적서 내용에서 견적 항목을 추출하여 JSON으로만 반환하세요.

견적서 내용:
{content}

응답 형식:
{{
  "items": [
    {{
      "name": "항목명",
      "specification": "규격 또는 사양",
      "quantity": 0,
      "unit": "단위",
      "unit_price": 0,
      "total_price": 0,
      "notes": "비고"
    }}
  ],
  "site_name": "현장명",
  "total_amount": 0
}}

규칙:
- 항목명이 없거나 단가가 0인 항목은 제외합니다.
- 숫자는 쉼표와 원 표시를 제거하고 숫자만 사용합니다.
- 합계가 없으면 quantity * unit_price로 계산합니다.
- 설명 문장 없이 JSON만 반환합니다.
"""


@dataclass
class ExtractedEstimate:
    items: list[dict] = field(default_factory=list)
    site_name: str = ""
    total_amount: float = 0.0


def extract_items(raw_content: dict) -> ExtractedEstimate:
    if not settings.gemini_api_key:
        raise RuntimeError("GEMINI_API_KEY가 설정되지 않았습니다.")

    content_text = _build_content_text(raw_content)
    client = genai.Client(api_key=settings.gemini_api_key)
    response = client.models.generate_content(
        model="gemini-1.5-flash",
        contents=EXTRACTION_PROMPT.format(content=content_text[:10000]),
    )

    return _parse_response(response.text or "")


def _build_content_text(raw_content: dict) -> str:
    text = raw_content.get("text", "")
    tables = raw_content.get("tables", [])
    if tables:
        table_lines = []
        for table in tables:
            for row in table:
                line = " | ".join(str(cell) for cell in row if cell)
                if line.strip():
                    table_lines.append(line)
        text += "\n\n[table data]\n" + "\n".join(table_lines)
    return text


def _parse_response(response_text: str) -> ExtractedEstimate:
    start = response_text.find("{")
    end = response_text.rfind("}") + 1
    if start == -1 or end <= start:
        return ExtractedEstimate()

    try:
        data = json.loads(response_text[start:end])
        return ExtractedEstimate(
            items=data.get("items", []),
            site_name=data.get("site_name", ""),
            total_amount=float(data.get("total_amount", 0) or 0),
        )
    except (json.JSONDecodeError, ValueError, TypeError):
        return ExtractedEstimate()
