from contextlib import asynccontextmanager
from datetime import date, datetime, timezone
from decimal import Decimal
import os
import time

from fastapi import Depends, FastAPI, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import Date, DateTime, ForeignKey, Integer, Numeric, String, create_engine, func, select
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker

DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL environment variable is required")

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine)


class Base(DeclarativeBase):
    pass


class Expense(Base):
    __tablename__ = "expenses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(120), nullable=False)
    category: Mapped[str] = mapped_column(String(60), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    spent_on: Mapped[date] = mapped_column(Date, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)


class ExpenseCreate(BaseModel):
    title: str = Field(min_length=1, max_length=120)
    category: str = Field(min_length=1, max_length=60)
    amount: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    spent_on: date = Field(default_factory=date.today)


class ExpenseRead(ExpenseCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime


class CategorySummary(BaseModel):
    category: str
    total: Decimal
    count: int


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Compose healthcheck normally handles readiness; retries provide resilience on cold starts.
    for attempt in range(20):
        try:
            Base.metadata.create_all(bind=engine)
            break
        except OperationalError:
            if attempt == 19:
                raise
            time.sleep(2)
    yield
    engine.dispose()


app = FastAPI(title="Expense Tracker API", description="Track expenses and see totals by category. Data is persisted in PostgreSQL.", version="1.0.0", lifespan=lifespan)


def get_db():
    with SessionLocal() as db:
        yield db


@app.get("/")
def root():
    return {"message": "Expense Tracker API is running", "docs": "/docs"}


@app.get("/health")
def health(db: Session = Depends(get_db)):
    db.execute(select(1))
    return {"status": "ok", "database": "connected"}


@app.post("/expenses", response_model=ExpenseRead, status_code=201)
def create_expense(payload: ExpenseCreate, db: Session = Depends(get_db)):
    expense = Expense(**payload.model_dump())
    db.add(expense)
    db.commit()
    db.refresh(expense)
    return expense


@app.get("/expenses", response_model=list[ExpenseRead])
def list_expenses(category: str | None = None, db: Session = Depends(get_db)):
    query = select(Expense)
    if category:
        query = query.where(Expense.category == category)
    return db.scalars(query.order_by(Expense.spent_on.desc(), Expense.id.desc())).all()


@app.get("/expenses/summary", response_model=list[CategorySummary])
def summary(db: Session = Depends(get_db)):
    rows = db.execute(
        select(Expense.category, func.sum(Expense.amount).label("total"), func.count(Expense.id).label("count"))
        .group_by(Expense.category)
        .order_by(func.sum(Expense.amount).desc())
    ).all()
    return [CategorySummary(category=row.category, total=row.total, count=row.count) for row in rows]


@app.get("/expenses/{expense_id}", response_model=ExpenseRead)
def get_expense(expense_id: int, db: Session = Depends(get_db)):
    expense = db.get(Expense, expense_id)
    if not expense:
        raise HTTPException(404, "Expense not found")
    return expense


@app.delete("/expenses/{expense_id}", status_code=204)
def delete_expense(expense_id: int, db: Session = Depends(get_db)):
    expense = db.get(Expense, expense_id)
    if not expense:
        raise HTTPException(404, "Expense not found")
    db.delete(expense)
    db.commit()
