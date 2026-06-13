from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import models, schemas, auth
from app.database import get_db

router = APIRouter(tags=["feedback"])


@router.post("/feedback", status_code=201)
def add_feedback(
    payload: schemas.FeedbackCreate,
    db: Session = Depends(get_db),
    current=Depends(auth.get_current_user),
):
    if db.get(models.Review, payload.review_id) is None:
        raise HTTPException(status_code=404, detail="Отзыв не найден")
    fb = models.Feedback(
        user_id=current.id,
        review_id=payload.review_id,
        is_useful=payload.is_useful,
    )
    db.add(fb)
    db.commit()
    return {"ok": True}
