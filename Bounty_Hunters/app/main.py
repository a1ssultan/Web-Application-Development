from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.database import Base, engine, get_db
from app.routers import criminals, hunts


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Tables normally come from db/init.sql; this only creates them if they are missing
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="Space Bounty Hunters API",
    description="Database of wanted criminals and a journal of bounty hunting attempts.",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(criminals.router)
app.include_router(hunts.router)


@app.get("/health", tags=["Health"], summary="API and database health check")
def health(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
    except SQLAlchemyError:
        raise HTTPException(status_code=503, detail="Database is not reachable")
    return {"status": "ok", "database": "connected"}
