from datetime import datetime
from pydantic import BaseModel, EmailStr, Field


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)
    display_name: str | None = None


class UserRead(BaseModel):
    id: int
    email: EmailStr
    display_name: str | None = None
    created_at: datetime
    model_config = {"from_attributes": True}


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class CritWeights(BaseModel):
    service: float = 0.25
    seller: float = 0.25
    product: float = 0.25
    delivery: float = 0.25


class ReviewCreate(BaseModel):
    product_id: int
    platform_id: int
    seller_id: int
    score_service: int = Field(ge=1, le=5)
    score_seller: int = Field(ge=1, le=5)
    score_product: int = Field(ge=1, le=5)
    score_delivery: int = Field(ge=1, le=5)
    comment_text: str | None = ""


class ReviewRead(BaseModel):
    id: int
    user_id: int
    product_id: int
    platform_id: int
    seller_id: int
    score_service: int
    score_seller: int
    score_product: int
    score_delivery: int
    score_total: float | None
    comment_text: str | None
    created_at: datetime
    model_config = {"from_attributes": True}


class CommentCreate(BaseModel):
    review_id: int
    text: str = Field(min_length=1)
    parent_comment_id: int | None = None


class CommentRead(BaseModel):
    id: int
    review_id: int
    user_id: int
    parent_comment_id: int | None
    text: str
    created_at: datetime
    replies: list["CommentRead"] = []
    model_config = {"from_attributes": True}


class FeedbackCreate(BaseModel):
    review_id: int
    is_useful: int = Field(ge=0, le=1, default=1)


class SearchResultItem(BaseModel):
    review_id: int
    product_id: int
    product_title: str
    category: str | None
    platform: str | None
    seller: str | None
    score_total: float | None
    relevance: float
    rank: float
    comment_text: str | None
    created_at: datetime


class NamedItem(BaseModel):
    id: int
    name: str
    model_config = {"from_attributes": True}
