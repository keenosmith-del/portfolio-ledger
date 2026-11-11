from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator


class Login(BaseModel):
    email: str = Field(min_length=3, max_length=200)
    password: str = Field(min_length=1, max_length=200)


class RunRequest(BaseModel):
    month: str = Field(pattern=r"^\d{4}-(0[1-9]|1[0-2])$")
    cutoff: datetime

    @field_validator("cutoff")
    @classmethod
    def aware_cutoff(cls, value: datetime) -> datetime:
        from app.db.models import now

        if value.tzinfo is None or value > now():
            raise ValueError("cutoff must be timezone-aware and not in the future")
        return value


class ReviewRequest(BaseModel):
    status: Literal["investigating", "resolved", "dismissed"]
    rationale: str = Field(min_length=5, max_length=1000)
