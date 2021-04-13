import asyncio
from typing import List

import fastapi
import uvicorn

from defiveyor import models
from defiveyor.utils import configure_logging

asgi_app = fastapi.FastAPI(title="Defiveyor API", version="2021.4")


@asgi_app.get("/assets", response_model=List[models.Asset])
async def get_assets():
    return [
        models.Asset(
            network="ethereum",
            protocol="curve",
            symbol="ETH",
            symbol_wrapped=None,
            apy_average_30days=0.02,
        )
    ]


@asgi_app.get("/pairs", response_model=List[models.AssetPair])
async def get_asset_pairs():
    return [
        models.AssetPair(
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
        access_log=True,
    )
    uvicorn_server = uvicorn.Server(config=uvicorn_config)
    uvicorn_server.install_signal_handlers = lambda *args: None
    # run non-blocking
    asyncio.get_event_loop().run_until_complete(uvicorn_server.serve())
