from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class CardVariant(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    issuer_name: str
    product_family: str
    display_name: str
    network: str
    market: str
    currency: str
    valid_from: date
    status: Literal["active", "historical", "unknown"]
    verification_status: Literal["synthetic", "unverified", "verified"]
    description: str = Field(min_length=1)
