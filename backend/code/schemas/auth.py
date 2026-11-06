from typing import Any, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class TokenResponse(BaseModel):
    """JWT authentication response returned after login or reauthentication."""

    token_type: str = Field(..., description="Token type, typically 'bearer'")
    outstanding_policies: list[Any] | None = Field(
        None, description="Policies the user has not yet agreed to"
    )
    access_token: str = Field(..., description="Signed JWT access token")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "token_type": "bearer",
                "outstanding_policies": None,
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyMSIsImV4cCI6MTcwMDAwMDAwMH0.abc123",
            }
        }
    )
