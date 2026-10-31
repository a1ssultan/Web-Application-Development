from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import HuntLog, WantedCriminal
from app.schemas import Coordinates, CriminalResponse, HuntLogCreate, LastKnownLocation


# ---------- Criminals ----------

def to_criminal_dict(criminal: WantedCriminal) -> dict:
    coordinates = None
    if criminal.latitude is not None and criminal.longitude is not None:
        coordinates = Coordinates(latitude=criminal.latitude, longitude=criminal.longitude)
    return CriminalResponse(
        id=criminal.id,
        name=criminal.name,
        nickname=criminal.nickname,
        reward=criminal.reward,
        last_known_location=LastKnownLocation(coordinates=coordinates, note=criminal.location_note),
        difficulty=criminal.difficulty,
        armed=criminal.armed,
        has_crew=criminal.has_crew,
        escape_master=criminal.escape_master,
    ).model_dump()


def get_criminals(
    db: Session,
    min_reward: int | None = None,
    max_reward: int | None = None,
    armed: bool | None = None,
    has_crew: bool | None = None,
    escape_master: bool | None = None,
    sort: str | None = None,
) -> list[WantedCriminal]:
    # Every filter is optional; the ones given are combined with AND
    query = select(WantedCriminal)
    if min_reward is not None:
        query = query.where(WantedCriminal.reward >= min_reward)
    if max_reward is not None:
        query = query.where(WantedCriminal.reward <= max_reward)
    if armed is not None:
        query = query.where(WantedCriminal.armed == armed)
    if has_crew is not None:
        query = query.where(WantedCriminal.has_crew == has_crew)
    if escape_master is not None:
        query = query.where(WantedCriminal.escape_master == escape_master)

    if sort == "reward":
        query = query.order_by(WantedCriminal.reward.asc(), WantedCriminal.id)
    elif sort == "-reward":
        query = query.order_by(WantedCriminal.reward.desc(), WantedCriminal.id)
    else:
        query = query.order_by(WantedCriminal.id)
    return list(db.scalars(query))


def get_criminal(db: Session, criminal_id: int) -> WantedCriminal | None:
    return db.get(WantedCriminal, criminal_id)


# ---------- Hunt logs ----------

def get_hunts(db: Session, criminal_id: int | None = None) -> list[HuntLog]:
    query = select(HuntLog).order_by(HuntLog.id)
    if criminal_id is not None:
        query = query.where(HuntLog.criminal_id == criminal_id)
    return list(db.scalars(query))


def get_hunt(db: Session, hunt_id: int) -> HuntLog | None:
    return db.get(HuntLog, hunt_id)


def create_hunt(db: Session, data: HuntLogCreate) -> HuntLog:
    hunt = HuntLog(**data.model_dump())  # created_at is filled by the database
    db.add(hunt)
    db.commit()
    db.refresh(hunt)
    return hunt


def update_hunt(db: Session, hunt: HuntLog, changes: dict) -> HuntLog:
    for field, value in changes.items():
        setattr(hunt, field, value)
    db.commit()
    db.refresh(hunt)
    return hunt


def delete_hunt(db: Session, hunt: HuntLog) -> None:
    db.delete(hunt)
    db.commit()
