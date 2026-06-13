from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Float,
    ForeignKey,
    DateTime,
    JSON,
    func,
)
from sqlalchemy.orm import relationship

from app.database import Base


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    display_name = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    profile_attrs = Column(JSON, default=dict)  # вектор x_u (CBF)
    crit_weights = Column(JSON, default=dict)  # веса критериев w_u

    reviews = relationship("Review", back_populates="user")
    comments = relationship("Comment", back_populates="user")
    feedback = relationship("Feedback", back_populates="user")


class Platform(Base):
    __tablename__ = "platforms"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)


class Category(Base):
    __tablename__ = "categories"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    parent_id = Column(Integer, ForeignKey("categories.id"), nullable=True)


class Seller(Base):
    __tablename__ = "sellers"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    platform_id = Column(Integer, ForeignKey("platforms.id"))


class Product(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False, index=True)
    description = Column(Text, default="")
    category_id = Column(Integer, ForeignKey("categories.id"))
    seller_id = Column(Integer, ForeignKey("sellers.id"))
    profile_attrs = Column(JSON, default=dict)  # вектор y_s (CBF)

    category = relationship("Category")
    seller = relationship("Seller")
    reviews = relationship("Review", back_populates="product")


class Review(Base):
    __tablename__ = "reviews"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    product_id = Column(Integer, ForeignKey("products.id"))
    platform_id = Column(Integer, ForeignKey("platforms.id"))
    seller_id = Column(Integer, ForeignKey("sellers.id"))
    # 4 критерия оценки (шкала 1..5)
    score_service = Column(Integer)  # сервис/площадка
    score_seller = Column(Integer)  # продавец
    score_product = Column(Integer)  # товар
    score_delivery = Column(Integer)  # доставка
    score_total = Column(Float)  # вычисляемая итоговая оценка
    comment_text = Column(Text, default="")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="reviews")
    product = relationship("Product", back_populates="reviews")
    comments = relationship("Comment", back_populates="review")


class Comment(Base):
    __tablename__ = "comments"
    id = Column(Integer, primary_key=True, index=True)
    review_id = Column(Integer, ForeignKey("reviews.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    parent_comment_id = Column(Integer, ForeignKey("comments.id"), nullable=True)
    text = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    review = relationship("Review", back_populates="comments")
    user = relationship("User", back_populates="comments")
    replies = relationship("Comment")


class Feedback(Base):
    """Обратная связь "отзыв полезен" — метка y_{u,s} для обучения FM/ANFIS."""

    __tablename__ = "feedback"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    review_id = Column(Integer, ForeignKey("reviews.id"))
    is_useful = Column(Integer, default=1)  # 1 = полезно, 0 = нет
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="feedback")
