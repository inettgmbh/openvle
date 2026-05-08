from typing import Any, List, Optional

from pydantic import BaseModel


class TokenResponse(BaseModel):
    token_type: str
    outstanding_policies: list[Any] | None = None
    access_token: str
