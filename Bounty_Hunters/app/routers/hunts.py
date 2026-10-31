from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app import crud
from app.database import get_db
from app.schemas import HuntLogCreate, HuntLogResponse, HuntLogUpdate

router = APIRouter(prefix="/api/hunts", tags=["Hunt Logs"])


def get_hunt_or_404(db: Session, hunt_id: int):
    hunt = crud.get_hunt(db, hunt_id)
    if hunt is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Hunt log {hunt_id} not found")
    return hunt


@router.get("/", response_model=list[HuntLogResponse], summary="List hunt logs")
def list_hunts(criminal_id: int | None = Query(default=None, gt=0), db: Session = Depends(get_db)):
    if criminal_id is not None and crud.get_criminal(db, criminal_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Criminal {criminal_id} not found")
    return crud.get_hunts(db, criminal_id)


@router.get("/{hunt_id}/", response_model=HuntLogResponse, summary="Get one hunt log")
def get_hunt(hunt_id: int, db: Session = Depends(get_db)):
    return get_hunt_or_404(db, hunt_id)


@router.post("/", response_model=HuntLogResponse, status_code=status.HTTP_201_CREATED, summary="Record a capture attempt")
def create_hunt(data: HuntLogCreate, db: Session = Depends(get_db)):
    if crud.get_criminal(db, data.criminal_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Criminal {data.criminal_id} not found")
    return crud.create_hunt(db, data)


@router.patch("/{hunt_id}/", response_model=HuntLogResponse, summary="Update success or notes")
def update_hunt(hunt_id: int, data: HuntLogUpdate, db: Session = Depends(get_db)):
    hunt = get_hunt_or_404(db, hunt_id)
    # Only fields that were sent with a value; null is not allowed for these columns
    changes = data.model_dump(exclude_none=True)
    if not changes:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Provide at least one of: success, notes")
    return crud.update_hunt(db, hunt, changes)


@router.delete("/{hunt_id}/", status_code=status.HTTP_204_NO_CONTENT, summary="Delete a hunt log")
def delete_hunt(hunt_id: int, db: Session = Depends(get_db)):
    crud.delete_hunt(db, get_hunt_or_404(db, hunt_id))
    return Response(status_code=status.HTTP_204_NO_CONTENT)
