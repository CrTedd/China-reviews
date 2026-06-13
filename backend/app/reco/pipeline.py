from typing import List, Optional

from sqlalchemy.orm import Session

from app import models
from app.config import settings
from app.reco.aggregate import aggregate_scores
from app.reco import cbf


def search_and_rank(
    db: Session,
    query: str = "",
    category: Optional[str] = None,
    sort: str = "relevance",
    order: str = "desc",
    user: Optional[models.User] = None,
    limit: int = 50,
) -> List[dict]:
    q_scores = aggregate_scores(db)

    weights = cbf.normalize_weights(user.crit_weights if user else None)
    user_profile = user.profile_attrs if user else None

    reviews = db.query(models.Review).all()

    products = {p.id: p for p in db.query(models.Product).all()}
    categories = {c.id: c.name for c in db.query(models.Category).all()}
    platforms = {p.id: p.name for p in db.query(models.Platform).all()}
    sellers = {s.id: s.name for s in db.query(models.Seller).all()}

    results = []
    for rv in reviews:
        product = products.get(rv.product_id)
        if product is None:
            continue
        cat_name = categories.get(product.category_id)

        if category and (not cat_name or category.lower() not in cat_name.lower()):
            continue

        q_s = q_scores.get(rv.product_id, [0.0, 0.0, 0.0, 0.0])

        document = " ".join(
            [product.title or "", product.description or "", rv.comment_text or ""]
        )
        relevance = cbf.text_relevance(query, document) if query else 0.0

        if query and relevance == 0.0:
            continue

        score_crit = cbf.score_crit(weights, q_s)
        sim = cbf.cosine_similarity(user_profile, product.profile_attrs)
        sim_norm = (sim + 1) / 2

        rank = (
            settings.rank_alpha_sim * sim_norm
            + settings.rank_beta_score * score_crit
            + settings.rank_gamma_relevance * relevance
        )

        results.append(
            {
                "review_id": rv.id,
                "product_id": rv.product_id,
                "product_title": product.title,
                "category": cat_name,
                "platform": platforms.get(rv.platform_id),
                "seller": sellers.get(rv.seller_id),
                "score_total": rv.score_total,
                "relevance": round(relevance, 4),
                "rank": round(rank, 4),
                "comment_text": rv.comment_text,
                "created_at": rv.created_at,
            }
        )

    reverse = order == "desc"
    if sort == "date":
        results.sort(key=lambda r: r["created_at"] or 0, reverse=reverse)
    elif sort == "score":
        results.sort(key=lambda r: r["score_total"] or 0, reverse=reverse)
    else:
        results.sort(key=lambda r: r["rank"], reverse=reverse)

    return results[:limit]
