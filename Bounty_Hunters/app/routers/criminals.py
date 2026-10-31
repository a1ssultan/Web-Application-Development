from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app import crud
from app.database import get_db
from app.schemas import CriminalDetailResponse, CriminalResponse, HuntLogResponse

router = APIRouter(prefix="/api/criminals", tags=["Wanted Criminals"])


@router.get("/", response_model=list[CriminalResponse], summary="List wanted criminals")
def list_criminals(
    min_reward: int | None = Query(default=None, ge=0),
    max_reward: int | None = Query(default=None, ge=0),
    armed: bool | None = None,
    has_crew: bool | None = None,
    escape_master: bool | None = None,
    sort: Literal["reward", "-reward"] | None = None,
    db: Session = Depends(get_db),
):
    if min_reward is not None and max_reward is not None and min_reward > max_reward:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "min_reward cannot be greater than max_reward")
    criminals = crud.get_criminals(db, min_reward, max_reward, armed, has_crew, escape_master, sort)
    return [crud.to_criminal_dict(c) for c in criminals]


@router.get("/{criminal_id}/", response_model=CriminalDetailResponse, summary="Get one criminal with hunt history")
def get_criminal(criminal_id: int, db: Session = Depends(get_db)):
    criminal = crud.get_criminal(db, criminal_id)
    if criminal is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Criminal {criminal_id} not found")
    hunts = [HuntLogResponse.model_validate(h) for h in sorted(criminal.hunts, key=lambda h: h.id)]
    return {**crud.to_criminal_dict(criminal), "hunts": hunts}
