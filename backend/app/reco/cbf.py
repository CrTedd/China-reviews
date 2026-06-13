import math
import re
from typing import Dict, List

WEIGHT_KEYS = ["service", "seller", "product", "delivery"]


def normalize_weights(weights: dict | None) -> List[float]:
    if not weights:
        return [0.25, 0.25, 0.25, 0.25]
    vec = [float(weights.get(k, 0.0)) for k in WEIGHT_KEYS]
    total = sum(vec)
    if total <= 0:
        return [0.25, 0.25, 0.25, 0.25]
    return [v / total for v in vec]


def score_crit(weights: List[float], q_s: List[float]) -> float:
    return float(sum(w * q for w, q in zip(weights, q_s)))


def cosine_similarity(x: dict | None, y: dict | None) -> float:
    if not x or not y:
        return 0.0
    keys = set(x) | set(y)
    xv = [float(x.get(k, 0.0)) for k in keys]
    yv = [float(y.get(k, 0.0)) for k in keys]
    dot = sum(a * b for a, b in zip(xv, yv))
    nx = math.sqrt(sum(a * a for a in xv))
    ny = math.sqrt(sum(b * b for b in yv))
    if nx == 0 or ny == 0:
        return 0.0
    return dot / (nx * ny)


_word_re = re.compile(r"\w+", re.UNICODE)


def _tokens(text: str) -> List[str]:
    return [t.lower() for t in _word_re.findall(text or "")]


def text_relevance(query: str, document: str) -> float:
    q = _tokens(query)
    if not q:
        return 0.0
    doc = set(_tokens(document))
    hits = sum(1 for w in q if w in doc)
    return hits / len(q)
