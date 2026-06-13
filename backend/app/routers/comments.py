from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import models, schemas, auth
from app.database import get_db

router = APIRouter(tags=["comments"])


@router.post("/comments", response_model=schemas.CommentRead, status_code=201)
def create_comment(
    payload: schemas.CommentCreate,
    db: Session = Depends(get_db),
    current=Depends(auth.get_current_user),
):
    if db.get(models.Review, payload.review_id) is None:
        raise HTTPException(status_code=404, detail="Отзыв не найден")
    comment = models.Comment(
        review_id=payload.review_id,
        user_id=current.id,
        parent_comment_id=payload.parent_comment_id,
        text=payload.text,
    )
    db.add(comment)
    db.commit()
    db.refresh(comment)
    return comment


@router.get("/reviews/{review_id}/comments", response_model=list[schemas.CommentRead])
def review_comments(review_id: int, db: Session = Depends(get_db)):
    flat = (
        db.query(models.Comment)
        .filter(models.Comment.review_id == review_id)
        .order_by(models.Comment.created_at.asc())
        .all()
    )
    nodes: dict[int, schemas.CommentRead] = {}
    roots: list[schemas.CommentRead] = []
    for c in flat:
        nodes[c.id] = schemas.CommentRead(
            id=c.id,
            review_id=c.review_id,
            user_id=c.user_id,
            parent_comment_id=c.parent_comment_id,
            text=c.text,
            created_at=c.created_at,
            replies=[],
        )
    for c in flat:
        node = nodes[c.id]
        if c.parent_comment_id and c.parent_comment_id in nodes:
            nodes[c.parent_comment_id].replies.append(node)
        else:
            roots.append(node)
    return roots
