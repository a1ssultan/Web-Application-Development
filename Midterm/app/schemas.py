from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

LockerSize = Literal["SMALL", "MEDIUM", "LARGE"]
RentalStatus = Literal["ACTIVE", "COMPLETED", "EXPIRED"]


class LockerCreate(BaseModel):
    number: str = Field(min_length=1, max_length=20, examples=["A-101"])
    size: LockerSize = Field(examples=["MEDIUM"])
    hourly_rate: Decimal = Field(gt=0, max_digits=10, decimal_places=2, examples=["500.00"])
    is_active: bool = True


class LockerUpdate(LockerCreate):
    pass


class LockerResponse(LockerCreate):
    id: int
    is_available: bool


class RentalCreate(BaseModel):
    locker_id: int = Field(gt=0, examples=[1])
    customer_name: str = Field(min_length=1, max_length=100, examples=["Aisultan K."])
    duration_hours: int = Field(gt=0, le=720, examples=[3])


class RentalUpdate(BaseModel):
    customer_name: str = Field(min_length=1, max_length=100, examples=["Aisultan Khalelov"])


class RentalResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    locker_id: int
    customer_name: str
    start_time: datetime
    end_time: datetime
    total_price: Decimal
    status: RentalStatus
