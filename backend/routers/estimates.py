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
