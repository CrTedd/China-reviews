from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app import models
from app.database import get_db

router = APIRouter(tags=["analytics"])


@router.get("/analytics/score-distribution")
def score_distribution(db: Session = Depends(get_db), product_id: int | None = None):
    query = db.query(models.Review)
    if product_id:
        query = query.filter(models.Review.product_id == product_id)
    buckets = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
    for rv in query.all():
        b = round(rv.score_total or 0)
        b = max(1, min(5, b))
        buckets[b] += 1
    return [{"score": k, "count": v} for k, v in buckets.items()]


@router.get("/analytics/criteria-avg")
def criteria_avg(db: Session = Depends(get_db), product_id: int | None = None):
    query = db.query(
        func.avg(models.Review.score_service),
        func.avg(models.Review.score_seller),
        func.avg(models.Review.score_product),
        func.avg(models.Review.score_delivery),
    )
    if product_id:
        query = query.filter(models.Review.product_id == product_id)
    row = query.one()
    labels = ["Сервис", "Продавец", "Товар", "Доставка"]
    return [
        {"criterion": labels[i], "avg": round(float(row[i] or 0), 2)} for i in range(4)
    ]


@router.get("/analytics/by-platform")
def by_platform(db: Session = Depends(get_db)):
    rows = (
        db.query(
            models.Platform.name,
            func.avg(models.Review.score_total),
            func.count(models.Review.id),
        )
        .join(models.Review, models.Review.platform_id == models.Platform.id)
        .group_by(models.Platform.name)
        .all()
    )
    return [
        {"platform": name, "avg": round(float(avg or 0), 2), "count": cnt}
        for name, avg, cnt in rows
    ]
