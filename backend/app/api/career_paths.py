from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import CareerPath

router = APIRouter(prefix="/api/career-paths", tags=["career-paths"])


@router.get("")
def list_career_paths(db: Session = Depends(get_db)) -> list[dict]:
    paths = db.query(CareerPath).order_by(CareerPath.id).all()
    by_id = {path.id: path for path in paths}
    previous_by_id: dict[int, CareerPath] = {}
    for path in paths:
        if path.next_step_id in by_id and path.next_step_id not in previous_by_id:
            previous_by_id[path.next_step_id] = path

    return [
        {
            "id": path.id,
            "name": path.name,
            "description": path.description,
            "next_step_id": path.next_step_id,
            "next_step_name": by_id[path.next_step_id].name if path.next_step_id in by_id else None,
            "previous_step_id": previous_by_id[path.id].id if path.id in previous_by_id else None,
            "previous_step_name": previous_by_id[path.id].name if path.id in previous_by_id else None,
        }
        for path in paths
    ]


__all__ = ["router"]
