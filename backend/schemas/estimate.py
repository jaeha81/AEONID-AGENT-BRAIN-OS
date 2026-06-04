from datetime import datetime

from pydantic import BaseModel, Field


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
    items: list[EstimateItemOut] = Field(default_factory=list)

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
