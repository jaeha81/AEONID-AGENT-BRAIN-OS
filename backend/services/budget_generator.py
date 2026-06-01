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
