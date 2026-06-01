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
