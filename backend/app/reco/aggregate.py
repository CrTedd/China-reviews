from collections import defaultdict
from typing import Dict, List

from sqlalchemy.orm import Session

from app import models

CRITERIA = ["score_service", "score_seller", "score_product", "score_delivery"]


def compute_user_authority(db: Session) -> Dict[int, float]:
    counts: Dict[int, set] = defaultdict(set)
    for r in db.query(models.Review.user_id, models.Review.product_id).all():
        counts[r.user_id].add(r.product_id)
    sizes = {uid: len(products) for uid, products in counts.items()}
    max_size = max(sizes.values()) if sizes else 1
    return {uid: (size / max_size if max_size else 0.0) for uid, size in sizes.items()}


def aggregate_scores(db: Session) -> Dict[int, List[float]]:
    authority = compute_user_authority(db)
    reviews = db.query(models.Review).all()

    weighted_sum: Dict[int, List[float]] = defaultdict(lambda: [0.0, 0.0, 0.0, 0.0])
    weight_total: Dict[int, float] = defaultdict(float)

    for rv in reviews:
        a = authority.get(rv.user_id, 0.0)
        if a == 0.0:
            a = 1e-6
        for i, crit in enumerate(CRITERIA):
            val = getattr(rv, crit) or 0
            weighted_sum[rv.product_id][i] += a * val
        weight_total[rv.product_id] += a

    raw: Dict[int, List[float]] = {}
    for pid, sums in weighted_sum.items():
        w = weight_total[pid] or 1.0
        raw[pid] = [s / w for s in sums]

    if not raw:
        return {}
    normalized: Dict[int, List[float]] = {pid: [0.0] * 4 for pid in raw}
    for i in range(4):
        col = [vals[i] for vals in raw.values()]
        lo, hi = min(col), max(col)
        span = (hi - lo) or 1.0
        for pid, vals in raw.items():
            normalized[pid][i] = (vals[i] - lo) / span
    return normalized
