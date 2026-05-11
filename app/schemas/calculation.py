# app/schemas/calculation.py
from enum import Enum
from pydantic import BaseModel, Field, ConfigDict, model_validator, field_validator
from typing import Optional
from uuid import UUID
from datetime import datetime


class CalculationType(str, Enum):
    """Valid calculation operation types."""
    ADDITION = "addition"
    SUBTRACTION = "subtraction"
    MULTIPLICATION = "multiplication"
    DIVISION = "division"


class CalculationBase(BaseModel):
    """
    Base schema shared by all calculation request/response schemas.
    Validates type (case-insensitive) and enforces no division by zero.
    """
    type: CalculationType = Field(..., description="Type of calculation", examples=["addition"])
    a: float = Field(..., description="First operand", examples=[10.0])
    b: float = Field(..., description="Second operand", examples=[5.0])

    @field_validator("type", mode="before")
    @classmethod
    def normalize_type(cls, v):
        allowed = {e.value for e in CalculationType}
        if not isinstance(v, str) or v.lower() not in allowed:
            raise ValueError(f"Type must be one of: {', '.join(sorted(allowed))}")
        return v.lower()

    @model_validator(mode='after')
    def check_no_division_by_zero(self) -> "CalculationBase":
        if self.type == CalculationType.DIVISION and self.b == 0:
            raise ValueError("Cannot divide by zero")
        return self

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "examples": [
                {"type": "addition", "a": 10.5, "b": 3.0},
                {"type": "division", "a": 100.0, "b": 5.0},
            ]
        }
    )


class CalculationCreate(CalculationBase):
    """
    Schema for creating a calculation. user_id is optional;
    if provided it must be a valid UUID referencing an existing user.
    """
    user_id: Optional[UUID] = Field(
        None,
        description="UUID of the owning user (optional)",
        examples=["123e4567-e89b-12d3-a456-426614174000"]
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "type": "addition",
                "a": 10.5,
                "b": 3.0,
                "user_id": "123e4567-e89b-12d3-a456-426614174000"
            }
        }
    )


class CalculationRead(CalculationBase):
    """
    Schema returned when reading a calculation from the database.
    Includes DB-generated fields: id, result, and timestamps.
    """
    id: UUID = Field(..., description="Unique UUID of the calculation")
    user_id: Optional[UUID] = Field(None, description="UUID of the owning user")
    result: float = Field(..., description="Computed result of the calculation")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last-updated timestamp")

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174999",
                "user_id": "123e4567-e89b-12d3-a456-426614174000",
                "type": "addition",
                "a": 10.5,
                "b": 3.0,
                "result": 13.5,
                "created_at": "2025-01-01T00:00:00",
                "updated_at": "2025-01-01T00:00:00",
            }
        }
    )


# Backward-compatible alias
CalculationResponse = CalculationRead


class CalculationUpdate(BaseModel):
    """Schema for updating operands on an existing calculation (partial update)."""
    a: Optional[float] = Field(None, description="Updated first operand")
    b: Optional[float] = Field(None, description="Updated second operand")

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={"example": {"a": 42.0, "b": 7.0}}
    )
