from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app import models
from app.database import get_db
from app.auth import oauth2_scheme
from app.config import settings
from app.reco.pipeline import search_and_rank
from jose import jwt, JWTError

router = APIRouter(tags=["search"])


def _optional_user(db: Session, token: str | None) -> models.User | None:
    if not token:
        return None
    try:
        payload = jwt.decode(
            token, settings.secret_key, algorithms=[settings.algorithm]
        )
        return db.get(models.User, int(payload.get("sub")))
    except (JWTError, TypeError, ValueError):
        return None


@router.get("/search")
def search(
    q: str = "",
    category: str | None = None,
    sort: str = "relevance",
    order: str = "desc",
    limit: int = 50,
    db: Session = Depends(get_db),
    authorization: str | None = None,
):
    user = _optional_user(db, authorization)
    items = search_and_rank(
        db, query=q, category=category, sort=sort, order=order, user=user, limit=limit
    )
    return {"count": len(items), "results": items}
