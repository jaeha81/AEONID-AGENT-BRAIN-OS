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
