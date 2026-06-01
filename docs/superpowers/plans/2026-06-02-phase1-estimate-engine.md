# Phase 1 견적 분석 엔진 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 견적서(PDF/Excel)를 업로드하면 Claude AI가 항목 추출 → 공정분리 → 실행예산 생성 → Obsidian Vault 저장까지 자동으로 처리하는 파이프라인 구축

**Architecture:** FastAPI 백엔드가 파일을 수신하여 pdfplumber/openpyxl로 파싱, Claude Sonnet으로 항목 추출, Claude Haiku로 공정 분류, 실행예산을 집계 후 Obsidian Vault에 Markdown으로 저장한다. Next.js 14 PWA가 파일 업로드 및 결과 조회 UI를 담당한다. SQLite로 처리 이력을 관리한다.

**Tech Stack:** Python 3.11, FastAPI, SQLAlchemy 2.0, SQLite, anthropic SDK, pdfplumber, openpyxl, pytest / Next.js 14, TypeScript, Tailwind CSS

---

## 파일 구조

```
d:\aeonid\
├── backend/
│   ├── main.py                    # FastAPI 앱 엔트리
│   ├── config.py                  # 환경변수 + 경로 설정
│   ├── database.py                # SQLAlchemy 세션
│   ├── requirements.txt
│   ├── models/
│   │   ├── __init__.py
│   │   └── estimate.py            # Estimate, EstimateItem, ProcessCategory ORM
│   ├── schemas/
│   │   ├── __init__.py
│   │   └── estimate.py            # Pydantic 요청/응답 스키마
│   ├── services/
│   │   ├── __init__.py
│   │   ├── document_parser.py     # PDF/Excel → raw text + tables
│   │   ├── ai_extractor.py        # Claude Sonnet → 구조화된 견적 항목
│   │   ├── process_classifier.py  # Claude Haiku → 공정 카테고리 분류
│   │   ├── budget_generator.py    # 분류된 항목 → 실행예산 집계
│   │   └── obsidian_writer.py     # 실행예산 → Obsidian Markdown 저장
│   ├── routers/
│   │   ├── __init__.py
│   │   └── estimates.py           # /estimates API 라우터
│   └── tests/
│       ├── conftest.py
│       ├── fixtures/
│       │   ├── sample_estimate.xlsx  # 테스트용 견적서 샘플
│       │   └── sample_estimate.pdf   # 테스트용 견적서 샘플
│       ├── test_document_parser.py
│       ├── test_ai_extractor.py
│       ├── test_process_classifier.py
│       ├── test_budget_generator.py
│       └── test_obsidian_writer.py
├── frontend/
│   ├── package.json
│   ├── next.config.js
│   ├── tsconfig.json
│   ├── tailwind.config.js
│   ├── public/
│   │   └── manifest.json
│   └── app/
│       ├── layout.tsx
│       ├── page.tsx               # 메인 대시보드
│       ├── globals.css
│       └── estimates/
│           ├── page.tsx           # 업로드 + 목록
│           └── [id]/
│               └── page.tsx       # 상세 + 실행예산
├── EONID-BRAIN/                   # Obsidian Vault
│   ├── 02_견적DB/
│   ├── 03_공정DB/
│   └── 06_실행예산DB/
└── docs/
    └── superpowers/
        └── plans/
            └── 2026-06-02-phase1-estimate-engine.md
```

---

## Task 1: 백엔드 프로젝트 초기 설정

**Files:**
- Create: `backend/requirements.txt`
- Create: `backend/config.py`
- Create: `backend/main.py`
- Create: `backend/database.py`

- [ ] **Step 1: requirements.txt 작성**

```
fastapi==0.115.0
uvicorn[standard]==0.30.0
sqlalchemy==2.0.35
pydantic==2.9.0
pydantic-settings==2.5.2
anthropic==0.40.0
pdfplumber==0.11.4
openpyxl==3.1.5
python-multipart==0.0.12
pytest==8.3.3
pytest-asyncio==0.24.0
httpx==0.27.2
```

- [ ] **Step 2: 의존성 설치**

```bash
cd backend
pip install -r requirements.txt
```

Expected: Successfully installed ... (에러 없이 완료)

- [ ] **Step 3: config.py 작성**

```python
from pydantic_settings import BaseSettings
from pathlib import Path

class Settings(BaseSettings):
    anthropic_api_key: str
    database_url: str = "sqlite:///./aeonid.db"
    obsidian_vault_path: str = str(Path(__file__).parent.parent / "EONID-BRAIN")
    upload_dir: str = str(Path(__file__).parent / "uploads")

    class Config:
        env_file = ".env"

settings = Settings()
```

- [ ] **Step 4: .env 파일 생성 (백엔드 루트)**

```
ANTHROPIC_API_KEY=sk-ant-...여기에_실제_키_입력
```

- [ ] **Step 5: database.py 작성**

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from .config import settings

engine = create_engine(settings.database_url, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class Base(DeclarativeBase):
    pass

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

- [ ] **Step 6: main.py 작성**

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import engine, Base
from .routers import estimates

Base.metadata.create_all(bind=engine)

app = FastAPI(title="AEONID Agent Brain OS", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(estimates.router, prefix="/estimates", tags=["estimates"])

@app.get("/health")
def health():
    return {"status": "ok"}
```

- [ ] **Step 7: 업로드 디렉토리 생성**

```bash
mkdir backend/uploads
mkdir backend/models
mkdir backend/schemas
mkdir backend/services
mkdir backend/routers
mkdir backend/tests
mkdir backend/tests/fixtures
touch backend/models/__init__.py
touch backend/schemas/__init__.py
touch backend/services/__init__.py
touch backend/routers/__init__.py
```

- [ ] **Step 8: 서버 기동 확인**

```bash
cd backend
uvicorn main:app --reload
```

브라우저에서 `http://localhost:8000/health` 접속 → `{"status":"ok"}` 확인

- [ ] **Step 9: 커밋**

```bash
git init
git add backend/requirements.txt backend/config.py backend/main.py backend/database.py
git commit -m "feat: FastAPI 백엔드 초기 설정"
```

---

## Task 2: DB 모델 및 Pydantic 스키마

**Files:**
- Create: `backend/models/estimate.py`
- Create: `backend/schemas/estimate.py`
- Create: `backend/models/__init__.py`

- [ ] **Step 1: 실패하는 테스트 작성**

`backend/tests/test_models.py`:
```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.database import Base
from backend.models.estimate import Estimate, EstimateItem

def test_estimate_model_creation():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    db = Session()

    est = Estimate(site_name="테스트현장", original_filename="test.pdf", status="pending")
    db.add(est)
    db.commit()
    db.refresh(est)

    assert est.id is not None
    assert est.site_name == "테스트현장"
    assert est.status == "pending"
    db.close()

def test_estimate_item_relationship():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    db = Session()

    est = Estimate(site_name="현장A", original_filename="a.pdf", status="pending")
    db.add(est)
    db.flush()

    item = EstimateItem(
        estimate_id=est.id,
        name="타일공사",
        specification="300x300",
        quantity=100,
        unit="장",
        unit_price=5000,
        total_price=500000,
        process_category="타일"
    )
    db.add(item)
    db.commit()

    assert len(est.items) == 1
    assert est.items[0].name == "타일공사"
    db.close()
```

- [ ] **Step 2: 테스트 실패 확인**

```bash
cd backend
pytest tests/test_models.py -v
```

Expected: `ImportError` 또는 `ModuleNotFoundError`

- [ ] **Step 3: ORM 모델 작성**

`backend/models/estimate.py`:
```python
from datetime import datetime
from sqlalchemy import String, Integer, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from ..database import Base

class Estimate(Base):
    __tablename__ = "estimates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    site_name: Mapped[str] = mapped_column(String(200), default="미지정현장")
    original_filename: Mapped[str] = mapped_column(String(500))
    file_path: Mapped[str | None] = mapped_column(String(500))
    status: Mapped[str] = mapped_column(String(50), default="pending")
    total_amount: Mapped[float] = mapped_column(Float, default=0.0)
    obsidian_estimate_path: Mapped[str | None] = mapped_column(String(500))
    obsidian_budget_path: Mapped[str | None] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    items: Mapped[list["EstimateItem"]] = relationship("EstimateItem", back_populates="estimate")

class EstimateItem(Base):
    __tablename__ = "estimate_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    estimate_id: Mapped[int] = mapped_column(ForeignKey("estimates.id"))
    name: Mapped[str] = mapped_column(String(200))
    specification: Mapped[str] = mapped_column(String(500), default="")
    quantity: Mapped[float] = mapped_column(Float, default=0.0)
    unit: Mapped[str] = mapped_column(String(50), default="")
    unit_price: Mapped[float] = mapped_column(Float, default=0.0)
    total_price: Mapped[float] = mapped_column(Float, default=0.0)
    process_category: Mapped[str] = mapped_column(String(100), default="기타")
    classification_confidence: Mapped[float] = mapped_column(Float, default=0.0)
    notes: Mapped[str] = mapped_column(Text, default="")

    estimate: Mapped["Estimate"] = relationship("Estimate", back_populates="items")
```

`backend/models/__init__.py`:
```python
from .estimate import Estimate, EstimateItem
```

- [ ] **Step 4: 테스트 통과 확인**

```bash
pytest tests/test_models.py -v
```

Expected: 2 tests PASSED

- [ ] **Step 5: Pydantic 스키마 작성**

`backend/schemas/estimate.py`:
```python
from pydantic import BaseModel
from datetime import datetime

class EstimateItemOut(BaseModel):
    id: int
    name: str
    specification: str
    quantity: float
    unit: str
    unit_price: float
    total_price: float
    process_category: str
    classification_confidence: float

    model_config = {"from_attributes": True}

class EstimateOut(BaseModel):
    id: int
    site_name: str
    original_filename: str
    status: str
    total_amount: float
    created_at: datetime
    items: list[EstimateItemOut] = []

    model_config = {"from_attributes": True}

class BudgetCategory(BaseModel):
    name: str
    subtotal: float
    item_count: int
    items: list[EstimateItemOut]

class BudgetOut(BaseModel):
    estimate_id: int
    site_name: str
    total_amount: float
    item_count: int
    categories: list[BudgetCategory]
    obsidian_estimate_path: str | None
    obsidian_budget_path: str | None
```

- [ ] **Step 6: 커밋**

```bash
git add backend/models/ backend/schemas/ backend/tests/test_models.py
git commit -m "feat: Estimate ORM 모델 및 Pydantic 스키마 추가"
```

---

## Task 3: 문서 파서 (PDF/Excel → raw content)

**Files:**
- Create: `backend/services/document_parser.py`
- Create: `backend/tests/test_document_parser.py`
- Create: `backend/tests/fixtures/` (테스트 파일)

- [ ] **Step 1: 실패하는 테스트 작성**

`backend/tests/test_document_parser.py`:
```python
import pytest
from pathlib import Path
from backend.services.document_parser import parse_document, ParsedDocument

FIXTURES_DIR = Path(__file__).parent / "fixtures"

def test_parse_excel_returns_text_and_tables():
    """Excel 파일 파싱 시 text와 tables를 반환한다."""
    # fixtures/sample.xlsx 생성
    import openpyxl
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(["항목명", "규격", "수량", "단위", "단가", "합계"])
    ws.append(["타일공사", "300x300", 100, "장", 5000, 500000])
    ws.append(["도배공사", "합지", 50, "롤", 30000, 1500000])
    wb.save(FIXTURES_DIR / "sample.xlsx")

    result = parse_document(str(FIXTURES_DIR / "sample.xlsx"))

    assert isinstance(result, ParsedDocument)
    assert "타일공사" in result.text
    assert len(result.tables) > 0
    assert result.tables[0][1][0] == "타일공사"

def test_parse_unsupported_format_raises():
    """지원하지 않는 확장자는 ValueError를 발생시킨다."""
    with pytest.raises(ValueError, match="Unsupported"):
        parse_document("file.docx")

def test_parsed_document_has_file_type():
    """ParsedDocument에 file_type 필드가 있다."""
    import openpyxl
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(["test", "data"])
    wb.save(FIXTURES_DIR / "type_test.xlsx")

    result = parse_document(str(FIXTURES_DIR / "type_test.xlsx"))
    assert result.file_type == "excel"
```

- [ ] **Step 2: 실패 확인**

```bash
pytest tests/test_document_parser.py -v
```

Expected: `ImportError: cannot import name 'parse_document'`

- [ ] **Step 3: 문서 파서 구현**

`backend/services/document_parser.py`:
```python
from dataclasses import dataclass, field
from pathlib import Path
import pdfplumber
import openpyxl

@dataclass
class ParsedDocument:
    text: str
    tables: list[list[list[str]]]
    file_type: str

def parse_document(file_path: str) -> ParsedDocument:
    """PDF 또는 Excel 견적서를 파싱하여 text와 tables를 반환한다."""
    path = Path(file_path)
    suffix = path.suffix.lower()

    if suffix == ".pdf":
        return _parse_pdf(path)
    elif suffix in (".xlsx", ".xls"):
        return _parse_excel(path)
    raise ValueError(f"Unsupported file type: {suffix}. 지원 형식: .pdf, .xlsx, .xls")

def _parse_pdf(path: Path) -> ParsedDocument:
    pages_text: list[str] = []
    tables: list[list[list[str]]] = []

    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                pages_text.append(text)
            for table in (page.extract_tables() or []):
                normalized = [
                    [str(cell or "").strip() for cell in row]
                    for row in table
                ]
                tables.append(normalized)

    return ParsedDocument(
        text="\n".join(pages_text),
        tables=tables,
        file_type="pdf"
    )

def _parse_excel(path: Path) -> ParsedDocument:
    wb = openpyxl.load_workbook(path, data_only=True)
    all_tables: list[list[list[str]]] = []
    text_lines: list[str] = []

    for sheet_name in wb.sheetnames:
        ws = wb[sheet_name]
        rows: list[list[str]] = []
        for row in ws.iter_rows():
            cells = [str(cell.value or "").strip() for cell in row]
            if any(c for c in cells):
                rows.append(cells)
                text_lines.append("\t".join(cells))
        if rows:
            all_tables.append(rows)

    return ParsedDocument(
        text="\n".join(text_lines),
        tables=all_tables,
        file_type="excel"
    )
```

- [ ] **Step 4: 테스트 통과 확인**

```bash
pytest tests/test_document_parser.py -v
```

Expected: 3 tests PASSED

- [ ] **Step 5: 커밋**

```bash
git add backend/services/document_parser.py backend/tests/test_document_parser.py
git commit -m "feat: PDF/Excel 문서 파서 구현"
```

---

## Task 4: AI 항목 추출기 (Claude Sonnet → 구조화된 항목)

**Files:**
- Create: `backend/services/ai_extractor.py`
- Create: `backend/tests/test_ai_extractor.py`

- [ ] **Step 1: 실패하는 테스트 작성**

`backend/tests/test_ai_extractor.py`:
```python
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
    """Claude API 응답을 파싱하여 ExtractedEstimate를 반환한다."""
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
    """Claude API가 잘못된 JSON을 반환해도 빈 결과를 반환한다."""
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
```

- [ ] **Step 2: 실패 확인**

```bash
pytest tests/test_ai_extractor.py -v
```

Expected: `ImportError`

- [ ] **Step 3: AI 추출기 구현**

`backend/services/ai_extractor.py`:
```python
import json
from dataclasses import dataclass, field
import anthropic

EXTRACTION_PROMPT = """당신은 인테리어 공사 견적서 분석 전문가입니다.
아래 견적서 내용에서 견적 항목들을 추출하여 JSON으로 반환하세요.

견적서 내용:
{content}

다음 JSON 형식으로만 응답하세요 (다른 설명 없이):
{{
  "items": [
    {{
      "name": "항목명",
      "specification": "규격/사양 (없으면 빈 문자열)",
      "quantity": 수량(숫자),
      "unit": "단위",
      "unit_price": 단가(숫자, 쉼표·원 표시 제거),
      "total_price": 합계(숫자, 쉼표·원 표시 제거),
      "notes": "비고 (없으면 빈 문자열)"
    }}
  ],
  "site_name": "현장명 (없으면 빈 문자열)",
  "total_amount": 견적총액(숫자)
}}

규칙:
- 항목명이 없거나 단가가 0인 항목은 제외
- 숫자는 쉼표·원 없이 순수 정수 또는 실수
- 합계가 없으면 quantity × unit_price로 계산"""

@dataclass
class ExtractedEstimate:
    items: list[dict] = field(default_factory=list)
    site_name: str = ""
    total_amount: float = 0.0

def extract_items(raw_content: dict) -> ExtractedEstimate:
    """Claude Sonnet을 사용하여 견적서 raw content에서 구조화된 항목을 추출한다."""
    content_text = _build_content_text(raw_content)

    client = anthropic.Anthropic()
    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4096,
        messages=[{
            "role": "user",
            "content": EXTRACTION_PROMPT.format(content=content_text[:10000])
        }]
    )

    response_text = message.content[0].text
    return _parse_response(response_text)

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
        text += "\n\n[테이블 데이터]\n" + "\n".join(table_lines)
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
            total_amount=float(data.get("total_amount", 0) or 0)
        )
    except (json.JSONDecodeError, ValueError):
        return ExtractedEstimate()
```

- [ ] **Step 4: 테스트 통과 확인**

```bash
pytest tests/test_ai_extractor.py -v
```

Expected: 2 tests PASSED

- [ ] **Step 5: 커밋**

```bash
git add backend/services/ai_extractor.py backend/tests/test_ai_extractor.py
git commit -m "feat: Claude Sonnet AI 견적 항목 추출기 구현"
```

---

## Task 5: 공정 분류기 (Claude Haiku → 공정 카테고리)

**Files:**
- Create: `backend/services/process_classifier.py`
- Create: `backend/tests/test_process_classifier.py`

- [ ] **Step 1: 실패하는 테스트 작성**

`backend/tests/test_process_classifier.py`:
```python
import pytest
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

def test_classify_items_returns_classifications(monkeypatch):
    """항목 리스트를 공정 카테고리로 분류한다."""
    mock_content = MagicMock()
    mock_content.text = MOCK_CLASSIFICATION_JSON
    mock_msg = MagicMock()
    mock_msg.content = [mock_content]
    mock_client = MagicMock()
    mock_client.messages.create.return_value = mock_msg

    with patch("backend.services.process_classifier.anthropic.Anthropic", return_value=mock_client):
        results = classify_items(SAMPLE_ITEMS)

    assert len(results) == 3
    assert all(isinstance(r, Classification) for r in results)
    assert results[0].category == "타일"
    assert results[0].confidence == 0.97
    assert results[1].category == "전기"

def test_classify_empty_list():
    """빈 리스트 입력 시 빈 리스트를 반환한다."""
    results = classify_items([])
    assert results == []

def test_process_categories_contains_required_keys():
    """PROCESS_CATEGORIES에 필수 공정 카테고리가 모두 있다."""
    required = ["철거", "설비", "전기", "타일", "도배", "페인트", "마루", "목공", "창호", "기타"]
    for cat in required:
        assert cat in PROCESS_CATEGORIES, f"'{cat}' 카테고리가 PROCESS_CATEGORIES에 없습니다"

def test_classify_handles_malformed_json(monkeypatch):
    """AI 응답이 잘못된 경우 '기타' 카테고리로 폴백한다."""
    mock_content = MagicMock()
    mock_content.text = "분류할 수 없습니다"
    mock_msg = MagicMock()
    mock_msg.content = [mock_content]
    mock_client = MagicMock()
    mock_client.messages.create.return_value = mock_msg

    with patch("backend.services.process_classifier.anthropic.Anthropic", return_value=mock_client):
        results = classify_items(SAMPLE_ITEMS)

    assert len(results) == 3
    assert all(r.category == "기타" for r in results)
    assert all(r.confidence == 0.0 for r in results)
```

- [ ] **Step 2: 실패 확인**

```bash
pytest tests/test_process_classifier.py -v
```

Expected: `ImportError`

- [ ] **Step 3: 공정 분류기 구현**

`backend/services/process_classifier.py`:
```python
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
    """Claude Haiku를 사용하여 견적 항목을 공정 카테고리로 분류한다."""
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
```

- [ ] **Step 4: 테스트 통과 확인**

```bash
pytest tests/test_process_classifier.py -v
```

Expected: 4 tests PASSED

- [ ] **Step 5: 커밋**

```bash
git add backend/services/process_classifier.py backend/tests/test_process_classifier.py
git commit -m "feat: Claude Haiku 공정 분류기 구현 (14개 카테고리)"
```

---

## Task 6: 실행예산 생성기

**Files:**
- Create: `backend/services/budget_generator.py`
- Create: `backend/tests/test_budget_generator.py`

- [ ] **Step 1: 실패하는 테스트 작성**

`backend/tests/test_budget_generator.py`:
```python
from backend.services.budget_generator import generate_budget, ExecutionBudget
from backend.services.process_classifier import Classification

SAMPLE_ITEMS = [
    {"name": "타일공사", "specification": "300x300", "quantity": 100, "unit": "장", "unit_price": 5000, "total_price": 500000, "notes": ""},
    {"name": "전기공사", "specification": "조명", "quantity": 1, "unit": "식", "unit_price": 1200000, "total_price": 1200000, "notes": ""},
    {"name": "도배공사", "specification": "합지", "quantity": 1, "unit": "식", "unit_price": 800000, "total_price": 800000, "notes": ""},
    {"name": "바닥타일", "specification": "600x600", "quantity": 50, "unit": "장", "unit_price": 15000, "total_price": 750000, "notes": ""},
]

SAMPLE_CLASSIFICATIONS = [
    Classification(item_index=0, category="타일", confidence=0.97, reason=""),
    Classification(item_index=1, category="전기", confidence=0.95, reason=""),
    Classification(item_index=2, category="도배", confidence=0.99, reason=""),
    Classification(item_index=3, category="타일", confidence=0.96, reason=""),
]

def test_generate_budget_aggregates_by_category():
    """카테고리별로 항목을 집계하여 실행예산을 생성한다."""
    budget = generate_budget(SAMPLE_ITEMS, SAMPLE_CLASSIFICATIONS)

    assert isinstance(budget, ExecutionBudget)
    assert budget.total_amount == 3250000
    assert budget.item_count == 4

    category_names = {cat.name for cat in budget.categories}
    assert "타일" in category_names
    assert "전기" in category_names
    assert "도배" in category_names

def test_tile_category_has_correct_subtotal():
    """타일 카테고리 소계가 두 항목의 합이다."""
    budget = generate_budget(SAMPLE_ITEMS, SAMPLE_CLASSIFICATIONS)
    tile_cat = next(c for c in budget.categories if c.name == "타일")

    assert tile_cat.subtotal == 1250000  # 500000 + 750000
    assert tile_cat.item_count == 2

def test_generate_budget_with_empty_items():
    """항목이 없으면 빈 예산을 반환한다."""
    budget = generate_budget([], [])

    assert budget.total_amount == 0
    assert budget.categories == []
    assert budget.item_count == 0

def test_categories_sorted_by_subtotal_desc():
    """카테고리는 소계 내림차순으로 정렬된다."""
    budget = generate_budget(SAMPLE_ITEMS, SAMPLE_CLASSIFICATIONS)
    subtotals = [c.subtotal for c in budget.categories]

    assert subtotals == sorted(subtotals, reverse=True)
```

- [ ] **Step 2: 실패 확인**

```bash
pytest tests/test_budget_generator.py -v
```

Expected: `ImportError`

- [ ] **Step 3: 실행예산 생성기 구현**

`backend/services/budget_generator.py`:
```python
from dataclasses import dataclass, field
from collections import defaultdict
from .process_classifier import Classification

@dataclass
class BudgetItem:
    name: str
    specification: str
    quantity: float
    unit: str
    unit_price: float
    total_price: float
    notes: str
    category: str
    confidence: float

@dataclass
class BudgetCategory:
    name: str
    items: list[BudgetItem] = field(default_factory=list)
    subtotal: float = 0.0
    item_count: int = 0

@dataclass
class ExecutionBudget:
    categories: list[BudgetCategory] = field(default_factory=list)
    total_amount: float = 0.0
    item_count: int = 0

def generate_budget(
    items: list[dict],
    classifications: list[Classification]
) -> ExecutionBudget:
    """분류된 견적 항목을 공정별로 집계하여 실행예산을 생성한다."""
    if not items:
        return ExecutionBudget()

    category_map = {c.item_index: c for c in classifications}
    category_groups: dict[str, list[BudgetItem]] = defaultdict(list)

    for i, item in enumerate(items):
        cls = category_map.get(i)
        category = cls.category if cls else "기타"
        confidence = cls.confidence if cls else 0.0

        budget_item = BudgetItem(
            name=item.get("name", ""),
            specification=item.get("specification", ""),
            quantity=float(item.get("quantity", 0) or 0),
            unit=item.get("unit", ""),
            unit_price=float(item.get("unit_price", 0) or 0),
            total_price=float(item.get("total_price", 0) or 0),
            notes=item.get("notes", ""),
            category=category,
            confidence=confidence,
        )
        category_groups[category].append(budget_item)

    budget_categories = []
    for cat_name, cat_items in category_groups.items():
        subtotal = sum(item.total_price for item in cat_items)
        budget_categories.append(BudgetCategory(
            name=cat_name,
            items=cat_items,
            subtotal=subtotal,
            item_count=len(cat_items),
        ))

    budget_categories.sort(key=lambda c: c.subtotal, reverse=True)
    total = sum(c.subtotal for c in budget_categories)

    return ExecutionBudget(
        categories=budget_categories,
        total_amount=total,
        item_count=len(items),
    )
```

- [ ] **Step 4: 테스트 통과 확인**

```bash
pytest tests/test_budget_generator.py -v
```

Expected: 4 tests PASSED

- [ ] **Step 5: 커밋**

```bash
git add backend/services/budget_generator.py backend/tests/test_budget_generator.py
git commit -m "feat: 실행예산 생성기 구현 (카테고리별 집계 + 소계 정렬)"
```

---

## Task 7: Obsidian 저장기 (실행예산 → Markdown)

**Files:**
- Create: `backend/services/obsidian_writer.py`
- Create: `backend/tests/test_obsidian_writer.py`

- [ ] **Step 1: 실패하는 테스트 작성**

`backend/tests/test_obsidian_writer.py`:
```python
import pytest
from pathlib import Path
from backend.services.obsidian_writer import write_to_obsidian, ObsidianPaths
from backend.services.budget_generator import ExecutionBudget, BudgetCategory, BudgetItem

@pytest.fixture
def tmp_vault(tmp_path):
    return str(tmp_path / "EONID-BRAIN")

@pytest.fixture
def sample_budget():
    items = [
        BudgetItem("타일공사", "300x300", 100, "장", 5000, 500000, "", "타일", 0.97),
        BudgetItem("전기공사", "조명", 1, "식", 1200000, 1200000, "", "전기", 0.95),
    ]
    return ExecutionBudget(
        categories=[
            BudgetCategory("전기", [items[1]], 1200000, 1),
            BudgetCategory("타일", [items[0]], 500000, 1),
        ],
        total_amount=1700000,
        item_count=2,
    )

def test_write_creates_estimate_and_budget_files(tmp_vault, sample_budget):
    """Obsidian vault에 견적DB와 실행예산DB 파일을 생성한다."""
    paths = write_to_obsidian(
        vault_path=tmp_vault,
        site_name="강남현장",
        date_str="2026-06-02",
        budget=sample_budget,
        original_items=[]
    )

    assert isinstance(paths, ObsidianPaths)
    assert Path(paths.estimate_path).exists()
    assert Path(paths.budget_path).exists()

def test_budget_file_contains_categories(tmp_vault, sample_budget):
    """실행예산 파일에 공정 카테고리와 소계가 포함된다."""
    paths = write_to_obsidian(
        vault_path=tmp_vault,
        site_name="강남현장",
        date_str="2026-06-02",
        budget=sample_budget,
        original_items=[]
    )

    content = Path(paths.budget_path).read_text(encoding="utf-8")
    assert "전기" in content
    assert "타일" in content
    assert "1,200,000" in content
    assert "1,700,000" in content

def test_budget_file_has_obsidian_frontmatter(tmp_vault, sample_budget):
    """파일에 Obsidian frontmatter(tags, date, site)가 포함된다."""
    paths = write_to_obsidian(
        vault_path=tmp_vault,
        site_name="강남현장",
        date_str="2026-06-02",
        budget=sample_budget,
        original_items=[]
    )

    content = Path(paths.budget_path).read_text(encoding="utf-8")
    assert "tags:" in content
    assert "실행예산" in content
    assert "강남현장" in content
    assert "date: 2026-06-02" in content

def test_write_creates_vault_subdirectories(tmp_vault, sample_budget):
    """vault 내 02_견적DB, 06_실행예산DB 디렉토리가 자동 생성된다."""
    write_to_obsidian(tmp_vault, "테스트현장", "2026-06-02", sample_budget, [])

    assert (Path(tmp_vault) / "02_견적DB").is_dir()
    assert (Path(tmp_vault) / "06_실행예산DB").is_dir()
```

- [ ] **Step 2: 실패 확인**

```bash
pytest tests/test_obsidian_writer.py -v
```

Expected: `ImportError`

- [ ] **Step 3: Obsidian 저장기 구현**

`backend/services/obsidian_writer.py`:
```python
from dataclasses import dataclass
from pathlib import Path
from .budget_generator import ExecutionBudget

@dataclass
class ObsidianPaths:
    estimate_path: str
    budget_path: str

def write_to_obsidian(
    vault_path: str,
    site_name: str,
    date_str: str,
    budget: ExecutionBudget,
    original_items: list[dict],
) -> ObsidianPaths:
    """실행예산과 견적 데이터를 Obsidian Vault Markdown 파일로 저장한다."""
    vault = Path(vault_path)

    estimate_dir = vault / "02_견적DB"
    estimate_dir.mkdir(parents=True, exist_ok=True)
    estimate_path = estimate_dir / f"{site_name}-{date_str}.md"
    estimate_path.write_text(
        _render_estimate(site_name, date_str, original_items, budget.total_amount),
        encoding="utf-8"
    )

    budget_dir = vault / "06_실행예산DB"
    budget_dir.mkdir(parents=True, exist_ok=True)
    budget_path = budget_dir / f"{site_name}-실행예산-{date_str}.md"
    budget_path.write_text(
        _render_budget(site_name, date_str, budget),
        encoding="utf-8"
    )

    return ObsidianPaths(
        estimate_path=str(estimate_path),
        budget_path=str(budget_path)
    )

def _render_estimate(
    site_name: str,
    date_str: str,
    items: list[dict],
    total: float
) -> str:
    rows = "\n".join(
        f"| {item.get('name','')} | {item.get('specification','')} | "
        f"{item.get('quantity','')} {item.get('unit','')} | "
        f"{_fmt(item.get('unit_price', 0))} | {_fmt(item.get('total_price', 0))} |"
        for item in items
    )
    return f"""---
tags: [견적, {site_name}]
date: {date_str}
site: {site_name}
total: {_fmt(total)}
---

# {site_name} 견적서

작성일: {date_str}
총 견적금액: {_fmt(total)}원

## 견적 항목

| 항목명 | 규격/사양 | 수량 | 단가 | 합계 |
|--------|----------|------|------|------|
{rows}

**총 견적금액: {_fmt(total)}원**
"""

def _render_budget(site_name: str, date_str: str, budget: ExecutionBudget) -> str:
    categories_text = ""
    for cat in budget.categories:
        rows = "\n".join(
            f"| {item.name} | {item.specification} | "
            f"{item.quantity} {item.unit} | "
            f"{_fmt(item.unit_price)} | {_fmt(item.total_price)} |"
            for item in cat.items
        )
        categories_text += f"""
## {cat.name} — 소계: {_fmt(cat.subtotal)}원

| 항목명 | 규격/사양 | 수량 | 단가 | 합계 |
|--------|----------|------|------|------|
{rows}

"""

    return f"""---
tags: [실행예산, {site_name}]
date: {date_str}
site: {site_name}
total: {_fmt(budget.total_amount)}
---

# {site_name} 실행예산

작성일: {date_str}
총 실행금액: {_fmt(budget.total_amount)}원
항목 수: {budget.item_count}개
{categories_text}
---
**총 실행예산: {_fmt(budget.total_amount)}원**
"""

def _fmt(value: float | int | None) -> str:
    if value is None:
        return "0"
    return f"{float(value):,.0f}"
```

- [ ] **Step 4: 테스트 통과 확인**

```bash
pytest tests/test_obsidian_writer.py -v
```

Expected: 4 tests PASSED

- [ ] **Step 5: 커밋**

```bash
git add backend/services/obsidian_writer.py backend/tests/test_obsidian_writer.py
git commit -m "feat: Obsidian Markdown 저장기 구현 (견적DB + 실행예산DB)"
```

---

## Task 8: FastAPI 엔드포인트 + 전체 파이프라인

**Files:**
- Create: `backend/routers/estimates.py`
- Create: `backend/tests/test_estimates_api.py`

- [ ] **Step 1: 실패하는 테스트 작성**

`backend/tests/test_estimates_api.py`:
```python
import pytest
from fastapi.testclient import TestClient
from pathlib import Path
from unittest.mock import patch, MagicMock
from backend.main import app
from backend.services.ai_extractor import ExtractedEstimate
from backend.services.process_classifier import Classification
from backend.services.budget_generator import ExecutionBudget, BudgetCategory, BudgetItem
from backend.services.obsidian_writer import ObsidianPaths

client = TestClient(app)

MOCK_EXTRACTED = ExtractedEstimate(
    items=[{"name": "타일공사", "specification": "300x300", "quantity": 100, "unit": "장", "unit_price": 5000, "total_price": 500000, "notes": ""}],
    site_name="강남현장",
    total_amount=500000
)
MOCK_CLASSIFICATIONS = [Classification(0, "타일", 0.97, "바닥타일")]
MOCK_BUDGET = ExecutionBudget(
    categories=[BudgetCategory("타일", [BudgetItem("타일공사","300x300",100,"장",5000,500000,"","타일",0.97)], 500000, 1)],
    total_amount=500000,
    item_count=1
)
MOCK_PATHS = ObsidianPaths("/vault/견적.md", "/vault/예산.md")

@pytest.fixture
def sample_excel(tmp_path):
    import openpyxl
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(["항목명", "규격", "수량", "단위", "단가", "합계"])
    ws.append(["타일공사", "300x300", 100, "장", 5000, 500000])
    path = tmp_path / "estimate.xlsx"
    wb.save(path)
    return path

def test_upload_estimate_returns_201(sample_excel):
    with patch("backend.routers.estimates.extract_items", return_value=MOCK_EXTRACTED), \
         patch("backend.routers.estimates.classify_items", return_value=MOCK_CLASSIFICATIONS), \
         patch("backend.routers.estimates.generate_budget", return_value=MOCK_BUDGET), \
         patch("backend.routers.estimates.write_to_obsidian", return_value=MOCK_PATHS):

        with open(sample_excel, "rb") as f:
            response = client.post(
                "/estimates/upload",
                files={"file": ("estimate.xlsx", f, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
            )

    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["site_name"] == "강남현장"
    assert data["status"] == "completed"

def test_get_estimate_budget_returns_budget(sample_excel):
    with patch("backend.routers.estimates.extract_items", return_value=MOCK_EXTRACTED), \
         patch("backend.routers.estimates.classify_items", return_value=MOCK_CLASSIFICATIONS), \
         patch("backend.routers.estimates.generate_budget", return_value=MOCK_BUDGET), \
         patch("backend.routers.estimates.write_to_obsidian", return_value=MOCK_PATHS):

        with open(sample_excel, "rb") as f:
            upload_resp = client.post(
                "/estimates/upload",
                files={"file": ("estimate.xlsx", f, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
            )
        est_id = upload_resp.json()["id"]

    budget_resp = client.get(f"/estimates/{est_id}/budget")
    assert budget_resp.status_code == 200
    data = budget_resp.json()
    assert "categories" in data
    assert data["total_amount"] == 500000

def test_get_nonexistent_estimate_returns_404():
    response = client.get("/estimates/99999/budget")
    assert response.status_code == 404
```

- [ ] **Step 2: 실패 확인**

```bash
pytest tests/test_estimates_api.py -v
```

Expected: `ImportError` 또는 연결 오류

- [ ] **Step 3: API 라우터 구현**

`backend/routers/estimates.py`:
```python
import shutil
from pathlib import Path
from datetime import datetime
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..database import get_db
from ..models.estimate import Estimate, EstimateItem
from ..schemas.estimate import EstimateOut, BudgetOut, BudgetCategory, EstimateItemOut
from ..services.document_parser import parse_document
from ..services.ai_extractor import extract_items
from ..services.process_classifier import classify_items
from ..services.budget_generator import generate_budget
from ..services.obsidian_writer import write_to_obsidian
from ..config import settings

router = APIRouter()

ALLOWED_EXTENSIONS = {".pdf", ".xlsx", ".xls"}

@router.post("/upload", response_model=EstimateOut, status_code=status.HTTP_201_CREATED)
async def upload_estimate(file: UploadFile = File(...), db: Session = Depends(get_db)):
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"지원 형식: {ALLOWED_EXTENSIONS}")

    upload_dir = Path(settings.upload_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    save_path = upload_dir / f"{ts}_{file.filename}"

    with open(save_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    estimate = Estimate(
        original_filename=file.filename or "",
        file_path=str(save_path),
        status="processing"
    )
    db.add(estimate)
    db.commit()
    db.refresh(estimate)

    try:
        raw = parse_document(str(save_path))
        extracted = extract_items({"text": raw.text, "tables": raw.tables})
        classifications = classify_items(extracted.items)
        budget = generate_budget(extracted.items, classifications)

        date_str = datetime.now().strftime("%Y-%m-%d")
        site_name = extracted.site_name or "미지정현장"
        paths = write_to_obsidian(
            vault_path=settings.obsidian_vault_path,
            site_name=site_name,
            date_str=date_str,
            budget=budget,
            original_items=extracted.items,
        )

        estimate.site_name = site_name
        estimate.total_amount = budget.total_amount
        estimate.status = "completed"
        estimate.obsidian_estimate_path = paths.estimate_path
        estimate.obsidian_budget_path = paths.budget_path

        for i, item in enumerate(extracted.items):
            cls = next((c for c in classifications if c.item_index == i), None)
            db.add(EstimateItem(
                estimate_id=estimate.id,
                name=item.get("name", ""),
                specification=item.get("specification", ""),
                quantity=float(item.get("quantity", 0) or 0),
                unit=item.get("unit", ""),
                unit_price=float(item.get("unit_price", 0) or 0),
                total_price=float(item.get("total_price", 0) or 0),
                process_category=cls.category if cls else "기타",
                classification_confidence=cls.confidence if cls else 0.0,
                notes=item.get("notes", ""),
            ))

    except Exception as exc:
        estimate.status = "failed"
        db.commit()
        raise HTTPException(status_code=500, detail=f"처리 실패: {str(exc)}") from exc

    db.commit()
    db.refresh(estimate)
    return estimate

@router.get("/{estimate_id}", response_model=EstimateOut)
def get_estimate(estimate_id: int, db: Session = Depends(get_db)):
    estimate = db.get(Estimate, estimate_id)
    if not estimate:
        raise HTTPException(status_code=404, detail="견적을 찾을 수 없습니다")
    return estimate

@router.get("/{estimate_id}/budget", response_model=BudgetOut)
def get_budget(estimate_id: int, db: Session = Depends(get_db)):
    estimate = db.get(Estimate, estimate_id)
    if not estimate:
        raise HTTPException(status_code=404, detail="견적을 찾을 수 없습니다")

    from collections import defaultdict
    category_groups: dict[str, list[EstimateItemOut]] = defaultdict(list)
    for item in estimate.items:
        category_groups[item.process_category].append(EstimateItemOut.model_validate(item))

    categories = [
        BudgetCategory(
            name=cat,
            subtotal=sum(i.total_price for i in items),
            item_count=len(items),
            items=items
        )
        for cat, items in category_groups.items()
    ]
    categories.sort(key=lambda c: c.subtotal, reverse=True)

    return BudgetOut(
        estimate_id=estimate.id,
        site_name=estimate.site_name,
        total_amount=estimate.total_amount,
        item_count=len(estimate.items),
        categories=categories,
        obsidian_estimate_path=estimate.obsidian_estimate_path,
        obsidian_budget_path=estimate.obsidian_budget_path,
    )
```

- [ ] **Step 4: conftest.py 추가 (테스트 DB 격리)**

`backend/tests/conftest.py`:
```python
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.main import app
from backend.database import Base, get_db

@pytest.fixture(autouse=True)
def override_db():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    TestSession = sessionmaker(bind=engine)

    def _get_test_db():
        db = TestSession()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = _get_test_db
    yield
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)
```

- [ ] **Step 5: 전체 테스트 실행**

```bash
pytest tests/ -v
```

Expected: 모든 테스트 PASSED (test_models 포함)

- [ ] **Step 6: 커밋**

```bash
git add backend/routers/estimates.py backend/tests/test_estimates_api.py backend/tests/conftest.py
git commit -m "feat: 견적 업로드 파이프라인 API 엔드포인트 완성"
```

---

## Task 9: 프론트엔드 Next.js PWA 설정

**Files:**
- Create: `frontend/package.json`
- Create: `frontend/next.config.js`
- Create: `frontend/tailwind.config.js`
- Create: `frontend/tsconfig.json`
- Create: `frontend/public/manifest.json`
- Create: `frontend/app/layout.tsx`
- Create: `frontend/app/globals.css`

- [ ] **Step 1: Next.js 프로젝트 생성**

```bash
cd d:\aeonid
npx create-next-app@latest frontend --typescript --tailwind --app --no-src-dir --no-eslint
```

선택 옵션:
- TypeScript: Yes
- Tailwind CSS: Yes  
- App Router: Yes
- 기타: No

- [ ] **Step 2: PWA 패키지 설치**

```bash
cd frontend
npm install next-pwa
npm install -D @types/node
```

- [ ] **Step 3: next.config.js 수정**

```javascript
const withPWA = require("next-pwa")({
  dest: "public",
  disable: process.env.NODE_ENV === "development",
});

/** @type {import('next').NextConfig} */
const nextConfig = {
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: "http://localhost:8000/:path*",
      },
    ];
  },
};

module.exports = withPWA(nextConfig);
```

- [ ] **Step 4: public/manifest.json 작성**

```json
{
  "name": "AEONID Brain OS",
  "short_name": "AEONID",
  "description": "이언아이디 AI 견적 분석 시스템",
  "start_url": "/",
  "display": "standalone",
  "background_color": "#0f172a",
  "theme_color": "#3b82f6",
  "icons": [
    { "src": "/icon-192.png", "sizes": "192x192", "type": "image/png" },
    { "src": "/icon-512.png", "sizes": "512x512", "type": "image/png" }
  ]
}
```

- [ ] **Step 5: app/layout.tsx 작성**

```tsx
import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "AEONID Brain OS",
  description: "이언아이디 AI 견적 분석 시스템",
  manifest: "/manifest.json",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ko">
      <body className={`${inter.className} bg-slate-900 text-white min-h-screen`}>
        <header className="border-b border-slate-700 px-6 py-4">
          <h1 className="text-xl font-bold text-blue-400">AEONID Brain OS</h1>
        </header>
        <main className="p-6">{children}</main>
      </body>
    </html>
  );
}
```

- [ ] **Step 6: 개발 서버 기동 확인**

```bash
cd frontend
npm run dev
```

브라우저에서 `http://localhost:3000` 접속 → 페이지 렌더링 확인

- [ ] **Step 7: 커밋**

```bash
git add frontend/
git commit -m "feat: Next.js 14 PWA 프론트엔드 초기 설정"
```

---

## Task 10: 파일 업로드 UI

**Files:**
- Create: `frontend/app/estimates/page.tsx`
- Create: `frontend/app/page.tsx`

- [ ] **Step 1: 메인 페이지 (대시보드)**

`frontend/app/page.tsx`:
```tsx
import Link from "next/link";

export default function Home() {
  return (
    <div className="max-w-2xl mx-auto mt-12">
      <h2 className="text-2xl font-bold mb-2">안녕하세요, 이언아이디입니다</h2>
      <p className="text-slate-400 mb-8">AI 기반 견적 분석 시스템에 오신 것을 환영합니다</p>
      <div className="grid grid-cols-1 gap-4">
        <Link
          href="/estimates"
          className="block p-6 bg-slate-800 rounded-xl border border-slate-700 hover:border-blue-500 transition-colors"
        >
          <h3 className="text-lg font-semibold text-blue-400 mb-1">견적 분석</h3>
          <p className="text-slate-400 text-sm">PDF/Excel 견적서를 업로드하여 공정분리 및 실행예산을 자동 생성합니다</p>
        </Link>
      </div>
    </div>
  );
}
```

- [ ] **Step 2: 견적 업로드 페이지**

`frontend/app/estimates/page.tsx`:
```tsx
"use client";

import { useState, useRef } from "react";
import { useRouter } from "next/navigation";

interface UploadResult {
  id: number;
  site_name: string;
  status: string;
  total_amount: number;
}

export default function EstimatesPage() {
  const [dragging, setDragging] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);
  const router = useRouter();

  const handleFile = async (file: File) => {
    const allowed = [".pdf", ".xlsx", ".xls"];
    const ext = "." + file.name.split(".").pop()?.toLowerCase();
    if (!allowed.includes(ext)) {
      setError("PDF 또는 Excel 파일만 업로드 가능합니다");
      return;
    }

    setUploading(true);
    setError(null);
    const form = new FormData();
    form.append("file", file);

    try {
      const res = await fetch("/api/estimates/upload", { method: "POST", body: form });
      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.detail || "업로드 실패");
      }
      const result: UploadResult = await res.json();
      router.push(`/estimates/${result.id}`);
    } catch (e) {
      setError(e instanceof Error ? e.message : "알 수 없는 오류");
    } finally {
      setUploading(false);
    }
  };

  const onDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragging(false);
    const file = e.dataTransfer.files[0];
    if (file) handleFile(file);
  };

  return (
    <div className="max-w-2xl mx-auto">
      <h2 className="text-xl font-bold mb-6">견적서 업로드</h2>

      <div
        onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
        onDragLeave={() => setDragging(false)}
        onDrop={onDrop}
        onClick={() => fileRef.current?.click()}
        className={`border-2 border-dashed rounded-xl p-12 text-center cursor-pointer transition-colors ${
          dragging ? "border-blue-400 bg-blue-400/10" : "border-slate-600 hover:border-slate-400"
        } ${uploading ? "opacity-50 pointer-events-none" : ""}`}
      >
        <input
          ref={fileRef}
          type="file"
          accept=".pdf,.xlsx,.xls"
          className="hidden"
          onChange={(e) => e.target.files?.[0] && handleFile(e.target.files[0])}
        />
        {uploading ? (
          <div>
            <div className="w-8 h-8 border-2 border-blue-400 border-t-transparent rounded-full animate-spin mx-auto mb-3" />
            <p className="text-slate-300">AI가 견적서를 분석 중입니다...</p>
            <p className="text-slate-500 text-sm mt-1">항목 추출 → 공정 분류 → 실행예산 생성</p>
          </div>
        ) : (
          <div>
            <p className="text-slate-300 text-lg mb-2">견적서를 드래그하거나 클릭하여 업로드</p>
            <p className="text-slate-500 text-sm">지원 형식: PDF, Excel (.xlsx, .xls)</p>
          </div>
        )}
      </div>

      {error && (
        <div className="mt-4 p-4 bg-red-900/50 border border-red-700 rounded-lg text-red-300">
          {error}
        </div>
      )}
    </div>
  );
}
```

- [ ] **Step 3: 브라우저에서 업로드 UI 확인**

`http://localhost:3000/estimates` 접속
- 드래그앤드롭 영역이 보이는지 확인
- 파일 선택 클릭이 동작하는지 확인

- [ ] **Step 4: 커밋**

```bash
git add frontend/app/page.tsx frontend/app/estimates/page.tsx
git commit -m "feat: 견적서 업로드 UI (드래그앤드롭)"
```

---

## Task 11: 실행예산 결과 뷰

**Files:**
- Create: `frontend/app/estimates/[id]/page.tsx`

- [ ] **Step 1: 실행예산 결과 페이지 작성**

`frontend/app/estimates/[id]/page.tsx`:
```tsx
"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";

interface BudgetItem {
  id: number;
  name: string;
  specification: string;
  quantity: number;
  unit: string;
  unit_price: number;
  total_price: number;
  classification_confidence: number;
}

interface BudgetCategory {
  name: string;
  subtotal: number;
  item_count: number;
  items: BudgetItem[];
}

interface BudgetData {
  estimate_id: number;
  site_name: string;
  total_amount: number;
  item_count: number;
  categories: BudgetCategory[];
  obsidian_budget_path: string | null;
}

const fmt = (n: number) => n.toLocaleString("ko-KR") + "원";

export default function EstimateDetailPage() {
  const { id } = useParams();
  const [budget, setBudget] = useState<BudgetData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [expanded, setExpanded] = useState<Set<string>>(new Set());

  useEffect(() => {
    fetch(`/api/estimates/${id}/budget`)
      .then((r) => r.ok ? r.json() : r.json().then((d) => Promise.reject(d.detail)))
      .then((data) => {
        setBudget(data);
        setExpanded(new Set(data.categories.map((c: BudgetCategory) => c.name)));
      })
      .catch((e) => setError(String(e)))
      .finally(() => setLoading(false));
  }, [id]);

  if (loading) return (
    <div className="flex items-center justify-center h-64">
      <div className="w-8 h-8 border-2 border-blue-400 border-t-transparent rounded-full animate-spin" />
    </div>
  );

  if (error) return (
    <div className="max-w-2xl mx-auto p-4 bg-red-900/50 border border-red-700 rounded-lg text-red-300">
      오류: {error}
    </div>
  );

  if (!budget) return null;

  const toggle = (name: string) => {
    setExpanded((prev) => {
      const next = new Set(prev);
      next.has(name) ? next.delete(name) : next.add(name);
      return next;
    });
  };

  return (
    <div className="max-w-4xl mx-auto">
      <div className="flex items-center gap-3 mb-6">
        <Link href="/estimates" className="text-slate-400 hover:text-white text-sm">← 목록</Link>
        <h2 className="text-xl font-bold">{budget.site_name} — 실행예산</h2>
      </div>

      <div className="grid grid-cols-3 gap-4 mb-8">
        <div className="bg-slate-800 rounded-xl p-4 border border-slate-700">
          <p className="text-slate-400 text-sm">총 실행금액</p>
          <p className="text-2xl font-bold text-blue-400">{fmt(budget.total_amount)}</p>
        </div>
        <div className="bg-slate-800 rounded-xl p-4 border border-slate-700">
          <p className="text-slate-400 text-sm">항목 수</p>
          <p className="text-2xl font-bold">{budget.item_count}개</p>
        </div>
        <div className="bg-slate-800 rounded-xl p-4 border border-slate-700">
          <p className="text-slate-400 text-sm">공정 수</p>
          <p className="text-2xl font-bold">{budget.categories.length}개</p>
        </div>
      </div>

      {budget.obsidian_budget_path && (
        <div className="mb-6 p-3 bg-green-900/30 border border-green-700 rounded-lg text-green-300 text-sm">
          Obsidian 저장 완료: {budget.obsidian_budget_path}
        </div>
      )}

      <div className="space-y-3">
        {budget.categories.map((cat) => (
          <div key={cat.name} className="bg-slate-800 rounded-xl border border-slate-700 overflow-hidden">
            <button
              onClick={() => toggle(cat.name)}
              className="w-full flex items-center justify-between p-4 hover:bg-slate-750 transition-colors"
            >
              <div className="flex items-center gap-3">
                <span className="font-semibold">{cat.name}</span>
                <span className="text-slate-400 text-sm">{cat.item_count}개 항목</span>
              </div>
              <div className="flex items-center gap-3">
                <span className="font-bold text-blue-400">{fmt(cat.subtotal)}</span>
                <span className="text-slate-400">{expanded.has(cat.name) ? "▲" : "▼"}</span>
              </div>
            </button>

            {expanded.has(cat.name) && (
              <div className="border-t border-slate-700 overflow-x-auto">
                <table className="w-full text-sm">
                  <thead className="bg-slate-700/50">
                    <tr>
                      <th className="text-left p-3 text-slate-400">항목명</th>
                      <th className="text-left p-3 text-slate-400">규격</th>
                      <th className="text-right p-3 text-slate-400">수량</th>
                      <th className="text-right p-3 text-slate-400">단가</th>
                      <th className="text-right p-3 text-slate-400">합계</th>
                    </tr>
                  </thead>
                  <tbody>
                    {cat.items.map((item) => (
                      <tr key={item.id} className="border-t border-slate-700/50 hover:bg-slate-700/30">
                        <td className="p-3">{item.name}</td>
                        <td className="p-3 text-slate-400">{item.specification}</td>
                        <td className="p-3 text-right">{item.quantity} {item.unit}</td>
                        <td className="p-3 text-right">{item.unit_price.toLocaleString("ko-KR")}</td>
                        <td className="p-3 text-right font-medium">{item.total_price.toLocaleString("ko-KR")}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
```

- [ ] **Step 2: 엔드투엔드 테스트**

1. `http://localhost:8000` (FastAPI) 와 `http://localhost:3000` (Next.js) 동시 기동
2. `http://localhost:3000/estimates` 접속
3. 실제 견적서 Excel/PDF 업로드
4. 리디렉션 후 실행예산 결과 확인:
   - 공정 카테고리별 항목 확인
   - 소계/총계 확인
   - Obsidian 저장 경로 확인
5. `EONID-BRAIN/02_견적DB/` 와 `EONID-BRAIN/06_실행예산DB/` 폴더에 Markdown 파일 생성 확인

- [ ] **Step 3: 최종 테스트 전체 실행**

```bash
cd backend
pytest tests/ -v --tb=short
```

Expected: 전체 PASSED

- [ ] **Step 4: 최종 커밋**

```bash
git add frontend/app/estimates/
git commit -m "feat: 실행예산 결과 뷰 (공정별 접기/펼치기 테이블)"
```

```bash
git add .
git commit -m "feat: Phase 1 견적 분석 엔진 완성 — 업로드→추출→공정분리→실행예산→Obsidian"
```

---

## Self-Review

### Spec 커버리지 점검

| 스펙 요구사항 | 구현 태스크 |
|---|---|
| 견적서 업로드 | Task 8 (POST /estimates/upload), Task 10 (Upload UI) |
| 항목 추출 | Task 4 (ai_extractor.py — Claude Sonnet) |
| 공정 자동 분리 | Task 5 (process_classifier.py — Claude Haiku) |
| 실행예산 생성 | Task 6 (budget_generator.py) |
| Obsidian 저장 | Task 7 (obsidian_writer.py) |
| PWA Dashboard | Task 9 (Next.js setup), Task 10-11 (pages) |
| PDF 지원 | Task 3 (pdfplumber) |
| Excel 지원 | Task 3 (openpyxl) |
| SQLite 이력 관리 | Task 1-2 (database.py + models) |

**누락 항목 없음.**

### Placeholder 스캔

- 모든 태스크에 실제 코드 포함
- "TBD" 또는 "TODO" 없음
- 모든 import가 정의된 모듈에서 옴

### 타입 일관성 점검

- `ExtractedEstimate.items` → `list[dict]` → `classify_items(items: list[dict])` ✓
- `Classification` dataclass → `generate_budget(items, classifications: list[Classification])` ✓
- `ExecutionBudget` → `write_to_obsidian(budget: ExecutionBudget)` ✓
- `ObsidianPaths.estimate_path/budget_path` → `estimate.obsidian_estimate_path/budget_path` ✓
- `BudgetOut`, `BudgetCategory`, `EstimateItemOut` Pydantic → API response ✓
