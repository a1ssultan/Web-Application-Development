from datetime import datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.models import Locker, Rental
from app.schemas import LockerCreate, LockerResponse, RentalCreate


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def calculate_price(hourly_rate: Decimal, duration_hours: int) -> Decimal:
    return hourly_rate * duration_hours


# ---------- Expiration and availability ----------

def expire_overdue_rentals(db: Session) -> None:
    """Mark ACTIVE rentals whose end_time has passed as EXPIRED."""
    db.execute(
        update(Rental)
        .where(Rental.status == "ACTIVE", Rental.end_time <= utc_now())
        .values(status="EXPIRED")
    )
    db.commit()


def occupied_locker_ids(db: Session) -> set[int]:
    # Checks end_time too, so the answer is correct even before expire_overdue_rentals() runs
    rows = db.scalars(
        select(Rental.locker_id).where(Rental.status == "ACTIVE", Rental.end_time > utc_now())
    )
    return set(rows)


def is_locker_occupied(db: Session, locker_id: int) -> bool:
    return locker_id in occupied_locker_ids(db)


def to_locker_response(locker: Locker, occupied: set[int]) -> LockerResponse:
    return LockerResponse(
        id=locker.id,
        number=locker.number,
        size=locker.size,
        hourly_rate=locker.hourly_rate,
        is_active=locker.is_active,
        is_available=locker.is_active and locker.id not in occupied,
    )


# ---------- Lockers ----------

def get_lockers(db: Session) -> list[Locker]:
    return list(db.scalars(select(Locker).order_by(Locker.id)))


def get_locker(db: Session, locker_id: int) -> Locker | None:
    return db.get(Locker, locker_id)


def get_locker_by_number(db: Session, number: str) -> Locker | None:
    return db.scalar(select(Locker).where(Locker.number == number))


def create_locker(db: Session, data: LockerCreate) -> Locker:
    locker = Locker(**data.model_dump())
    db.add(locker)
    db.commit()
    db.refresh(locker)
    return locker


def update_locker(db: Session, locker: Locker, data: LockerCreate) -> Locker:
    for field, value in data.model_dump().items():
        setattr(locker, field, value)
    db.commit()
    db.refresh(locker)
    return locker


def locker_has_rentals(db: Session, locker_id: int) -> bool:
    return db.scalar(select(Rental.id).where(Rental.locker_id == locker_id).limit(1)) is not None


def delete_locker(db: Session, locker: Locker) -> None:
    db.delete(locker)
    db.commit()


# ---------- Rentals ----------

def get_rentals(db: Session) -> list[Rental]:
    return list(db.scalars(select(Rental).order_by(Rental.id)))


def get_rental(db: Session, rental_id: int) -> Rental | None:
    return db.get(Rental, rental_id)


def lock_locker(db: Session, locker_id: int) -> Locker | None:
    """SELECT ... FOR UPDATE: lock the locker row until this transaction commits.

    If two requests try to rent the same locker at the same time, the second one
    waits here until the first commits, and then sees the new ACTIVE rental.
    """
    return db.scalar(select(Locker).where(Locker.id == locker_id).with_for_update())


def create_rental(db: Session, locker: Locker, data: RentalCreate) -> Rental:
    start = utc_now()
    end = start + timedelta(hours=data.duration_hours)
    rental = Rental(
        locker_id=locker.id,
        customer_name=data.customer_name,
        start_time=start,
        end_time=end,
        total_price=calculate_price(locker.hourly_rate, data.duration_hours),
        status="ACTIVE",
    )
    db.add(rental)
    db.commit()  # commit also releases the row lock
    db.refresh(rental)
    return rental


def update_rental_name(db: Session, rental: Rental, customer_name: str) -> Rental:
    rental.customer_name = customer_name
    db.commit()
    db.refresh(rental)
    return rental


def complete_rental(db: Session, rental: Rental) -> Rental:
    rental.status = "COMPLETED"
    db.commit()
    db.refresh(rental)
    return rental


def delete_rental(db: Session, rental: Rental) -> None:
    db.delete(rental)
    db.commit()
