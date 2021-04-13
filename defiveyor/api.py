import asyncio
from typing import List, Optional

import fastapi
from pydantic import BaseModel
import uvicorn

from defiveyor.utils import configure_logging


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


asgi_app = fastapi.FastAPI(title="Defiveyor API", version="2021.4")


@asgi_app.get("/assets", response_model=List[Asset])
async def get_assets():
    return [
        Asset(
            network="ethereum",
            protocol="curve",
            symbol="ETH",
            symbol_wrapped=None,
            apy_average_30days=0.02,
        )
    ]


@asgi_app.get("/pairs", response_model=List[AssetPair])
async def get_asset_pairs():
    return [
        AssetPair(
            network="ethereum",
            protocol="uniswap-v2",
            symbol_0="ETH",
            symbol_0_wrapped="WETH",
            symbol_1="BTC",
            symbol_1_wrapped="WBTC",
            apy_average_30days=0.02,
        )
    ]


if __name__ == "__main__":
    configure_logging()
    uvicorn_config = uvicorn.Config(
        app=asgi_app,
        host="0.0.0.0",
        port=7777,
        log_config=None,
        log_level=None,
        access_log=False,
    )
    uvicorn_server = uvicorn.Server(config=uvicorn_config)
    uvicorn_server.install_signal_handlers = lambda *args: None
    # run non-blocking
    asyncio.get_event_loop().run_until_complete(uvicorn_server.serve())
