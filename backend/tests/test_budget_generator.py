from backend.services.budget_generator import ExecutionBudget, generate_budget
from backend.services.process_classifier import Classification

SAMPLE_ITEMS = [
    {"name": "타일공사", "specification": "300x300", "quantity": 100, "unit": "장", "unit_price": 5000, "total_price": 500000, "notes": ""},
    {"name": "전기공사", "specification": "조명", "quantity": 1, "unit": "식", "unit_price": 1200000, "total_price": 1200000, "notes": ""},
    {"name": "필름공사", "specification": "문짝", "quantity": 1, "unit": "식", "unit_price": 800000, "total_price": 800000, "notes": ""},
    {"name": "바닥타일", "specification": "600x600", "quantity": 50, "unit": "장", "unit_price": 15000, "total_price": 750000, "notes": ""},
]

SAMPLE_CLASSIFICATIONS = [
    Classification(item_index=0, category="타일", confidence=0.97, reason=""),
    Classification(item_index=1, category="전기", confidence=0.95, reason=""),
    Classification(item_index=2, category="필름", confidence=0.99, reason=""),
    Classification(item_index=3, category="타일", confidence=0.96, reason=""),
]


def test_generate_budget_aggregates_by_category():
    budget = generate_budget(SAMPLE_ITEMS, SAMPLE_CLASSIFICATIONS)

    assert isinstance(budget, ExecutionBudget)
    assert budget.total_amount == 3250000
    assert budget.item_count == 4

    category_names = {cat.name for cat in budget.categories}
    assert "타일" in category_names
    assert "전기" in category_names
    assert "필름" in category_names


def test_tile_category_has_correct_subtotal():
    budget = generate_budget(SAMPLE_ITEMS, SAMPLE_CLASSIFICATIONS)
    tile_cat = next(c for c in budget.categories if c.name == "타일")

    assert tile_cat.subtotal == 1250000
    assert tile_cat.item_count == 2


def test_generate_budget_with_empty_items():
    budget = generate_budget([], [])

    assert budget.total_amount == 0
    assert budget.categories == []
    assert budget.item_count == 0


def test_categories_sorted_by_subtotal_desc():
    budget = generate_budget(SAMPLE_ITEMS, SAMPLE_CLASSIFICATIONS)
    subtotals = [c.subtotal for c in budget.categories]

    assert subtotals == sorted(subtotals, reverse=True)
