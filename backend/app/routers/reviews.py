from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import models, schemas, auth
from app.database import get_db

router = APIRouter(tags=["reviews"])


@router.get("/platforms", response_model=list[schemas.NamedItem])
def list_platforms(db: Session = Depends(get_db)):
    return db.query(models.Platform).all()


@router.get("/categories", response_model=list[schemas.NamedItem])
def list_categories(db: Session = Depends(get_db)):
    return db.query(models.Category).all()


@router.get("/sellers", response_model=list[schemas.NamedItem])
def list_sellers(db: Session = Depends(get_db)):
    return db.query(models.Seller).all()


@router.get("/products")
def list_products(db: Session = Depends(get_db), limit: int = 100):
    rows = db.query(models.Product).limit(limit).all()
    return [
        {
            "id": p.id,
            "title": p.title,
            "description": p.description,
            "category_id": p.category_id,
            "seller_id": p.seller_id,
        }
        for p in rows
    ]


@router.post("/reviews", response_model=schemas.ReviewRead, status_code=201)
def create_review(
    payload: schemas.ReviewCreate,
    db: Session = Depends(get_db),
    current=Depends(auth.get_current_user),
):
    total = (
        payload.score_service
        + payload.score_seller
        + payload.score_product
        + payload.score_delivery
    ) / 4.0
    review = models.Review(
        user_id=current.id,
        product_id=payload.product_id,
        platform_id=payload.platform_id,
        seller_id=payload.seller_id,
        score_service=payload.score_service,
        score_seller=payload.score_seller,
        score_product=payload.score_product,
        score_delivery=payload.score_delivery,
        score_total=total,
        comment_text=payload.comment_text or "",
    )
    db.add(review)
    db.commit()
    db.refresh(review)
    return review


@router.get("/reviews/{review_id}", response_model=schemas.ReviewRead)
def get_review(review_id: int, db: Session = Depends(get_db)):
    review = db.get(models.Review, review_id)
    if review is None:
        raise HTTPException(status_code=404, detail="Отзыв не найден")
    return review


@router.get("/products/{product_id}/reviews", response_model=list[schemas.ReviewRead])
def product_reviews(product_id: int, db: Session = Depends(get_db)):
    return (
        db.query(models.Review)
        .filter(models.Review.product_id == product_id)
        .order_by(models.Review.created_at.desc())
        .all()
    )
