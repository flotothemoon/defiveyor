import asyncio
import logging
from typing import List, Optional, Tuple

import fastapi
from pydantic import BaseModel
import uvicorn

from defiveyor.ingest import ingest, RecordList
from defiveyor.utils import configure_logging

UPDATE_STATE_INTERVAL_SECONDS = 60 * 60  # once per hour

logger = logging.getLogger("api")


class Asset(BaseModel):
    network: str
    protocol: str
    symbol: str
    symbol_wrapped: Optional[str]
    apy: float


class AssetPair(BaseModel):
    network: str
    protocol: str
    symbol_0: str
    symbol_0_wrapped: Optional[str]
    symbol_1: str
    symbol_1_wrapped: Optional[str]
    apy: float


asgi_app = fastapi.FastAPI(title="Defiveyor API", version="2021.4")


@asgi_app.get("/v1/assets", response_model=List[Asset])
async def get_assets():
    return asgi_app.state.assets


@asgi_app.get("/v1/pairs", response_model=List[AssetPair])
async def get_asset_pairs():
    return asgi_app.state.asset_pairs


async def _update_ingest() -> Tuple[List[Asset], List[AssetPair]]:
    records: RecordList = await ingest()
    assets: List[Asset] = []
    asset_pairs: List[AssetPair] = []
    for record in records:
        if len(record.assets) == 1:
            assets.append(Asset(
                network=record.network.value,
                protocol=record.protocol.value,
                symbol=record.assets[0].asset.value,
                symbol_wrapped=record.assets[0].wrapped_symbol,
                apy=record.apy,
            ))
        elif len(record.assets) == 2:
            asset_pairs.append(AssetPair(
                network=record.network.value,
                protocol=record.protocol.value,
                symbol_0=record.assets[0].asset.value,
                symbol_0_wrapped=record.assets[0].wrapped_symbol,
                symbol_1=record.assets[1].asset.value,
                symbol_1_wrapped=record.assets[1].wrapped_symbol,
                apy=record.apy,
            ))
    return assets, asset_pairs


@asgi_app.on_event('startup')
async def _init():
    await _update_state()
    asyncio.create_task(_update_state_loop())


async def _update_state():
    logger.info("updating state from ingest")
    assets, asset_pairs = await _update_ingest()
    asgi_app.state.assets = assets
    asgi_app.state.asset_pairs = asset_pairs
    logger.info("update done")


async def _update_state_loop():
    while True:
        logger.info(f"waiting {UPDATE_STATE_INTERVAL_SECONDS}s for next update")
        await asyncio.sleep(UPDATE_STATE_INTERVAL_SECONDS)
        await _update_state()


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
