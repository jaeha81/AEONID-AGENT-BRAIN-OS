from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from backend.services.ai_extractor import ExtractedEstimate
from backend.services.budget_generator import BudgetCategory, BudgetItem, ExecutionBudget
from backend.services.obsidian_writer import ObsidianPaths
from backend.services.process_classifier import Classification

MOCK_EXTRACTED = ExtractedEstimate(
    items=[
        {
            "name": "타일공사",
            "specification": "300x300",
            "quantity": 100,
            "unit": "장",
            "unit_price": 5000,
            "total_price": 500000,
            "notes": "",
        }
    ],
    site_name="강남현장",
    total_amount=500000,
)
MOCK_CLASSIFICATIONS = [Classification(0, "타일", 0.97, "바닥타일")]
MOCK_BUDGET = ExecutionBudget(
    categories=[
        BudgetCategory(
            "타일",
            [BudgetItem("타일공사", "300x300", 100, "장", 5000, 500000, "", "타일", 0.97)],
            500000,
            1,
        )
    ],
    total_amount=500000,
    item_count=1,
)
MOCK_PATHS = ObsidianPaths("/vault/견적.md", "/vault/예산.md")


@pytest.fixture
def sample_excel(tmp_path: Path):
    import openpyxl

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(["항목명", "규격", "수량", "단위", "단가", "합계"])
    ws.append(["타일공사", "300x300", 100, "장", 5000, 500000])
    path = tmp_path / "estimate.xlsx"
    wb.save(path)
    return path


def test_upload_estimate_returns_201(client, sample_excel):
    with patch("backend.routers.estimates.parse_document") as mock_parse, \
         patch("backend.routers.estimates.extract_items", return_value=MOCK_EXTRACTED), \
         patch("backend.routers.estimates.classify_items", return_value=MOCK_CLASSIFICATIONS), \
         patch("backend.routers.estimates.generate_budget", return_value=MOCK_BUDGET), \
         patch("backend.routers.estimates.write_to_obsidian", return_value=MOCK_PATHS):

        mock_parse.return_value = MagicMock(text="타일공사", tables=[])

        with open(sample_excel, "rb") as f:
            response = client.post(
                "/estimates/upload",
                files={
                    "file": (
                        "estimate.xlsx",
                        f,
                        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    )
                },
            )

    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["site_name"] == "강남현장"
    assert data["status"] == "completed"


def test_get_estimate_budget_returns_budget(client, sample_excel):
    with patch("backend.routers.estimates.parse_document") as mock_parse, \
         patch("backend.routers.estimates.extract_items", return_value=MOCK_EXTRACTED), \
         patch("backend.routers.estimates.classify_items", return_value=MOCK_CLASSIFICATIONS), \
         patch("backend.routers.estimates.generate_budget", return_value=MOCK_BUDGET), \
         patch("backend.routers.estimates.write_to_obsidian", return_value=MOCK_PATHS):

        mock_parse.return_value = MagicMock(text="타일공사", tables=[])

        with open(sample_excel, "rb") as f:
            upload_resp = client.post(
                "/estimates/upload",
                files={
                    "file": (
                        "estimate.xlsx",
                        f,
                        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    )
                },
            )
        est_id = upload_resp.json()["id"]

    budget_resp = client.get(f"/estimates/{est_id}/budget")
    assert budget_resp.status_code == 200
    data = budget_resp.json()
    assert "categories" in data
    assert data["total_amount"] == 500000


def test_get_nonexistent_estimate_returns_404(client):
    response = client.get("/estimates/99999/budget")
    assert response.status_code == 404
