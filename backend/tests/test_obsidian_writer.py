from pathlib import Path

import pytest

from backend.services.budget_generator import BudgetCategory, BudgetItem, ExecutionBudget
from backend.services.obsidian_writer import ObsidianPaths, write_to_obsidian


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
    paths = write_to_obsidian(
        vault_path=tmp_vault,
        site_name="강남현장",
        date_str="2026-06-02",
        budget=sample_budget,
        original_items=[],
    )

    assert isinstance(paths, ObsidianPaths)
    assert Path(paths.estimate_path).exists()
    assert Path(paths.budget_path).exists()


def test_budget_file_contains_categories(tmp_vault, sample_budget):
    paths = write_to_obsidian(
        vault_path=tmp_vault,
        site_name="강남현장",
        date_str="2026-06-02",
        budget=sample_budget,
        original_items=[],
    )

    content = Path(paths.budget_path).read_text(encoding="utf-8")
    assert "전기" in content
    assert "타일" in content
    assert "1,200,000" in content
    assert "1,700,000" in content


def test_budget_file_has_obsidian_frontmatter(tmp_vault, sample_budget):
    paths = write_to_obsidian(
        vault_path=tmp_vault,
        site_name="강남현장",
        date_str="2026-06-02",
        budget=sample_budget,
        original_items=[],
    )

    content = Path(paths.budget_path).read_text(encoding="utf-8")
    assert "tags:" in content
    assert "실행예산" in content
    assert "강남현장" in content
    assert "date: 2026-06-02" in content


def test_write_creates_vault_subdirectories(tmp_vault, sample_budget):
    write_to_obsidian(tmp_vault, "테스트현장", "2026-06-02", sample_budget, [])

    assert (Path(tmp_vault) / "02_견적DB").is_dir()
    assert (Path(tmp_vault) / "06_실행예산DB").is_dir()
