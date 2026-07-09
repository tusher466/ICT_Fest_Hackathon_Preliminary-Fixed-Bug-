"""Pydantic request/response models."""

from pydantic import BaseModel, Field, ConfigDict


class RegisterRequest(BaseModel):
    org_name: str = Field(..., min_length=1, max_length=100)
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6, max_length=128)


class LoginRequest(BaseModel):
    org_name: str = Field(..., min_length=1, max_length=100)
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6, max_length=128)


class RefreshRequest(BaseModel):
    refresh_token: str = Field(..., min_length=1)


class RoomCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    capacity: int = Field(..., ge=1)
    hourly_rate_cents: int = Field(..., ge=1)


class BookingCreateRequest(BaseModel):
    room_id: int = Field(..., ge=1)
    start_time: str = Field(..., min_length=1)
    end_time: str = Field(..., min_length=1)

    model_config = ConfigDict(extra="forbid")
