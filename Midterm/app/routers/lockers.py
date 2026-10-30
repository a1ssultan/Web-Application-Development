from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app import crud
from app.database import get_db
from app.schemas import LockerCreate, LockerResponse, LockerUpdate

router = APIRouter(prefix="/lockers", tags=["Lockers"])


def get_locker_or_404(db: Session, locker_id: int):
    locker = crud.get_locker(db, locker_id)
    if locker is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Locker {locker_id} not found")
    return locker


@router.get("", response_model=list[LockerResponse], summary="List all lockers")
def list_lockers(db: Session = Depends(get_db)):
    crud.expire_overdue_rentals(db)
    occupied = crud.occupied_locker_ids(db)
    return [crud.to_locker_response(locker, occupied) for locker in crud.get_lockers(db)]


# Declared before "/{locker_id}" so "available" is not treated as an ID
@router.get("/available", response_model=list[LockerResponse], summary="List available lockers")
def list_available_lockers(db: Session = Depends(get_db)):
    crud.expire_overdue_rentals(db)
    occupied = crud.occupied_locker_ids(db)
    lockers = [crud.to_locker_response(locker, occupied) for locker in crud.get_lockers(db)]
    return [locker for locker in lockers if locker.is_available]


@router.get("/{locker_id}", response_model=LockerResponse, summary="Get a locker by ID")
def get_locker(locker_id: int, db: Session = Depends(get_db)):
    locker = get_locker_or_404(db, locker_id)
    crud.expire_overdue_rentals(db)
    return crud.to_locker_response(locker, crud.occupied_locker_ids(db))


@router.post("", response_model=LockerResponse, status_code=status.HTTP_201_CREATED, summary="Create a locker")
def create_locker(data: LockerCreate, db: Session = Depends(get_db)):
    if crud.get_locker_by_number(db, data.number):
        raise HTTPException(status.HTTP_409_CONFLICT, f"Locker number '{data.number}' already exists")
    locker = crud.create_locker(db, data)
    return crud.to_locker_response(locker, set())


@router.put("/{locker_id}", response_model=LockerResponse, summary="Update a locker")
def update_locker(locker_id: int, data: LockerUpdate, db: Session = Depends(get_db)):
    locker = get_locker_or_404(db, locker_id)
    same_number = crud.get_locker_by_number(db, data.number)
    if same_number and same_number.id != locker_id:
        raise HTTPException(status.HTTP_409_CONFLICT, f"Locker number '{data.number}' already exists")
    locker = crud.update_locker(db, locker, data)
    return crud.to_locker_response(locker, crud.occupied_locker_ids(db))


@router.delete("/{locker_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete a locker")
def delete_locker(locker_id: int, db: Session = Depends(get_db)):
    locker = get_locker_or_404(db, locker_id)
    if crud.locker_has_rentals(db, locker_id):
        raise HTTPException(status.HTTP_409_CONFLICT, "Locker has rental history and cannot be deleted")
    crud.delete_locker(db, locker)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
