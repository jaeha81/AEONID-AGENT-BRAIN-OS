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
