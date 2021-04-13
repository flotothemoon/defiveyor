from typing import Optional

from pydantic import BaseModel


class Asset(BaseModel):
    network: str
    protocol: str
    symbol: str
    symbol_wrapped: Optional[str]
    apy_average_30days: float


class AssetPair(BaseModel):
    network: str
    protocol: str
    symbol_0: str
    symbol_0_wrapped: Optional[str]
    symbol_1: str
    symbol_1_wrapped: Optional[str]
    apy_average_30days: float
