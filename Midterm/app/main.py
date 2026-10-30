from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.database import Base, engine, get_db
from app.routers import lockers, rentals


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Creates the tables if they do not exist yet (no migrations needed for this project)
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="Storage Locker Management API",
    description="Manage storage lockers and rentals in malls, train stations and airports.",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(lockers.router)
app.include_router(rentals.router)


@app.get("/health", tags=["Health"], summary="API and database health check")
def health(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
    except SQLAlchemyError:
        raise HTTPException(status_code=503, detail="Database is not reachable")
    return {"status": "ok", "database": "connected"}
