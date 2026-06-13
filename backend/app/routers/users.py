from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app import models, schemas, auth
from app.database import get_db

router = APIRouter(tags=["users"])


@router.post("/auth/register", response_model=schemas.UserRead, status_code=201)
def register(payload: schemas.UserCreate, db: Session = Depends(get_db)):
    exists = db.query(models.User).filter(models.User.email == payload.email).first()
    if exists:
        raise HTTPException(status_code=400, detail="Email уже зарегистрирован")
    user = models.User(
        email=payload.email,
        password_hash=auth.hash_password(payload.password),
        display_name=payload.display_name or payload.email.split("@")[0],
        profile_attrs={},
        crit_weights={
            "service": 0.25,
            "seller": 0.25,
            "product": 0.25,
            "delivery": 0.25,
        },
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/auth/login", response_model=schemas.Token)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    user = db.query(models.User).filter(models.User.email == form_data.username).first()
    if not user or not auth.verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный email или пароль",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = auth.create_access_token(user.id)
    return schemas.Token(access_token=token)


@router.get("/users/me", response_model=schemas.UserRead)
def me(current=Depends(auth.get_current_user)):
    return current


@router.put("/users/me/weights")
def set_weights(
    weights: schemas.CritWeights,
    db: Session = Depends(get_db),
    current=Depends(auth.get_current_user),
):
    current.crit_weights = weights.model_dump()
    db.commit()
    return {"ok": True, "crit_weights": current.crit_weights}
