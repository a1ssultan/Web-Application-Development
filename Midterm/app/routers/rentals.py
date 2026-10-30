from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app import crud
from app.database import get_db
from app.schemas import RentalCreate, RentalResponse, RentalUpdate

router = APIRouter(prefix="/rentals", tags=["Rentals"])


def get_rental_or_404(db: Session, rental_id: int):
    rental = crud.get_rental(db, rental_id)
    if rental is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Rental {rental_id} not found")
    return rental


@router.get("", response_model=list[RentalResponse], summary="List all rentals")
def list_rentals(db: Session = Depends(get_db)):
    crud.expire_overdue_rentals(db)
    return crud.get_rentals(db)


@router.get("/{rental_id}", response_model=RentalResponse, summary="Get a rental by ID")
def get_rental(rental_id: int, db: Session = Depends(get_db)):
    crud.expire_overdue_rentals(db)
    return get_rental_or_404(db, rental_id)


@router.post("", response_model=RentalResponse, status_code=status.HTTP_201_CREATED, summary="Rent a locker")
def create_rental(data: RentalCreate, db: Session = Depends(get_db)):
    crud.expire_overdue_rentals(db)

    # Row lock on the locker: concurrent requests for the same locker run one after another
    locker = crud.lock_locker(db, data.locker_id)
    if locker is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Locker {data.locker_id} not found")
    if not locker.is_active:
        raise HTTPException(status.HTTP_409_CONFLICT, "Locker is not active")
    if crud.is_locker_occupied(db, locker.id):
        raise HTTPException(status.HTTP_409_CONFLICT, "Locker is already occupied")

    return crud.create_rental(db, locker, data)


@router.put("/{rental_id}", response_model=RentalResponse, summary="Update customer name")
def update_rental(rental_id: int, data: RentalUpdate, db: Session = Depends(get_db)):
    crud.expire_overdue_rentals(db)
    rental = get_rental_or_404(db, rental_id)
    return crud.update_rental_name(db, rental, data.customer_name)


@router.post("/{rental_id}/complete", response_model=RentalResponse, summary="Complete a rental")
def complete_rental(rental_id: int, db: Session = Depends(get_db)):
    crud.expire_overdue_rentals(db)
    rental = get_rental_or_404(db, rental_id)
    if rental.status != "ACTIVE":
        raise HTTPException(status.HTTP_409_CONFLICT, f"Rental is already {rental.status}")
    return crud.complete_rental(db, rental)


@router.delete("/{rental_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete a finished rental")
def delete_rental(rental_id: int, db: Session = Depends(get_db)):
    crud.expire_overdue_rentals(db)
    rental = get_rental_or_404(db, rental_id)
    if rental.status == "ACTIVE":
        raise HTTPException(status.HTTP_409_CONFLICT, "Active rental cannot be deleted; complete it first")
    crud.delete_rental(db, rental)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
