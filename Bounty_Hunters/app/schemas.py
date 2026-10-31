from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class Coordinates(BaseModel):
    latitude: float
    longitude: float


class LastKnownLocation(BaseModel):
    coordinates: Coordinates | None
    note: str | None


class HuntLogCreate(BaseModel):
    # extra="forbid": a client-supplied "created_at" or "id" is rejected with 422
    model_config = ConfigDict(extra="forbid")

    criminal_id: int = Field(gt=0, examples=[3])
    success: bool = Field(examples=[False])
    notes: str = Field(min_length=1, max_length=2000, examples=["Target escaped through an asteroid field."])


class HuntLogUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    success: bool | None = Field(default=None, examples=[True])
    notes: str | None = Field(default=None, min_length=1, max_length=2000, examples=["Captured on the second try."])


class HuntLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    criminal_id: int
    success: bool
    notes: str
    created_at: datetime


class CriminalResponse(BaseModel):
    id: int
    name: str | None
    nickname: str
    reward: int
    last_known_location: LastKnownLocation
    difficulty: int
    armed: bool
    has_crew: bool
    escape_master: bool


class CriminalDetailResponse(CriminalResponse):
    hunts: list[HuntLogResponse]
