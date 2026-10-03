from __future__ import annotations

from sqlalchemy import func
from sqlalchemy.orm import Session


def next_id(db: Session, model, prefix: str, pad: int = 2) -> str:
    """Generate the next sequential id for a model with ids like 'ALC-01'.

    Looks at the highest existing numeric suffix for the given prefix and
    returns prefix + (max + 1), zero-padded. Simple and good enough for a
    single-process SQLite prototype (not safe under concurrent writers,
    which this app does not have).
    """
    rows = db.query(model.id).filter(model.id.like(f"{prefix}-%")).all()
    max_n = 0
    for (rid,) in rows:
        try:
            n = int(rid.split("-")[-1])
        except ValueError:
            continue
        max_n = max(max_n, n)
    return f"{prefix}-{str(max_n + 1).zfill(pad)}"


def count_rows(db: Session, model) -> int:
    return db.query(func.count(model.id)).scalar() or 0
