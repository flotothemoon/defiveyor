import asyncio
import logging
from typing import List, Optional, Tuple, Union, Set, Iterable

import fastapi
from pydantic import BaseModel, Field
import uvicorn

from defiveyor import supported
from defiveyor.ingest import ingest, RecordList
from defiveyor.supported import Network, Protocol, Asset, RiskProfile
from defiveyor.utils import configure_logging

UPDATE_STATE_INTERVAL_SECONDS = 60 * 60  # once per hour

logger = logging.getLogger("api")


class AssetBase(BaseModel):
    network: Network = Field(..., description="name of the underlying network")
    protocol: Protocol = Field(..., description="name of the protocol")
    apy: float = Field(..., description="estimated annual percentage yield")
    risk_profile: RiskProfile = Field(
        ..., description="the risk associated with this holding"
    )

    @property
    def assets(self) -> Set[Asset]:
        raise NotImplementedError


class AssetSingle(AssetBase):
    kind: str = "single"
    symbol: Asset = Field(..., description="native symbol of the asset")
    symbol_wrapped: Optional[str] = Field(
        ..., description="wrapped symbol of the asset in this network & protocol"
    )

    @property
    def assets(self) -> Set[Asset]:
        return {self.symbol}

    class Config:
        schema_extra = {
            "example": {
                "network": "ethereum",
                "protocol": "compound",
                "symbol": "BTC",
                "symbol_wrapped": "WBTC",
                "apy": 0.0023,
                "risk_profile": "medium"
            }
        }


class AssetPair(AssetBase):
    kind: str = "pair"
    symbol_0: Asset = Field(..., description="native symbol of the asset")
    symbol_0_wrapped: Optional[str] = Field(
        ..., description="wrapped symbol of the asset in this network & protocol"
    )
    symbol_1: Asset = Field(..., description="native symbol of the asset")
    symbol_1_wrapped: Optional[str] = Field(
        ..., description="wrapped symbol of the asset in this network & protocol"
    )

    @property
    def assets(self) -> Set[Asset]:
        return {self.symbol_0, self.symbol_1}

    class Config:
        schema_extra = {
            "example": {
                "network": "ethereum",
                "protocol": "uniswap-v2",
                "symbol_0": "BTC",
                "symbol_0_wrapped": "WBTC",
                "symbol_1": "ETH",
                "symbol_1_wrapped": "WETH",
                "apy": 0.07,
                "risk_profile": "high"
            }
        }


def _filter_bases(
    bases: Iterable[AssetBase],
    asset: Optional[Asset] = None,
    protocol: Optional[Protocol] = None,
) -> Iterable[AssetBase]:
    return [
        base
        for base in bases
        if (asset is None or asset in base.assets)
        and (protocol is None or protocol == base.protocol)
    ]


asgi_app = fastapi.FastAPI(
    title="Defiveyor API",
    version="2021.4",
    description=(
        "A **free and open** API for DeFi return rates on various assets across protocols.\n"
        "\n"
        " - **No API keys or tokens are required**. Use responsibly.\n\n"
        " - APY is updated about once per hour and is not averaged over time.\n\n"
        f" - Supported Networks: {', '.join([network.value for network in supported.Network])}\n\n"
        f" - Supported Protocols: {', '.join([protocol.value for protocol in supported.Protocol])}\n\n"
        f" - Supported Assets: {', '.join([asset.value for asset in supported.Asset])}\n\n"
        " - The source code is available on [GitHub](https://github.com/flotothemoon/defiveyor).\n\n"
        "\n"
        "Provided by [Cryptoveyor](https://www.cryptoveyor.com),"
        " which does the same but for all kinds of ecosystem events.\n"
        "\n"
    ),
)


@asgi_app.get(
    "/v1/apy/all",
    summary="Get APY for single and paired assets, sorted by APY descending",
    response_model=List[Union[AssetSingle, AssetPair]],
)
async def get_all(asset: Optional[Asset] = None, protocol: Optional[Protocol] = None):
    return _filter_bases(asgi_app.state.combined, asset, protocol)


@asgi_app.get(
    "/v1/apy/assets",
    summary="Get APY for single assets, sorted by APY descending",
    response_model=List[AssetSingle],
)
async def get_assets(
    asset: Optional[Asset] = None, protocol: Optional[Protocol] = None
):
    return _filter_bases(asgi_app.state.assets, asset, protocol)


@asgi_app.get(
    "/v1/apy/pairs",
    summary="Get APY for asset pairs, sorted by APY descending",
    response_model=List[AssetPair],
)
async def get_asset_pairs(
    asset: Optional[Asset] = None, protocol: Optional[Protocol] = None
):
    return _filter_bases(asgi_app.state.asset_pairs, asset, protocol)


def _get_risk_profile_for_single(asset: Asset) -> RiskProfile:
    if asset.is_stable:
        return RiskProfile.Low
    else:
        return RiskProfile.High


def _get_risk_profile_for_pair(asset_0: Asset, asset_1: Asset) -> RiskProfile:
    if asset_0.is_stable:
        if asset_1.is_stable:
            return RiskProfile.Low
        else:
            return RiskProfile.Medium
    else:
        return RiskProfile.High


async def _update_ingest() -> Tuple[List[AssetSingle], List[AssetPair]]:
    records: RecordList = await ingest()
    assets: List[AssetSingle] = []
    asset_pairs: List[AssetPair] = []
    for record in records:
        if len(record.assets) == 1:
            assets.append(
                AssetSingle(
                    network=record.network,
                    protocol=record.protocol,
                    symbol=record.assets[0].asset,
                    symbol_wrapped=record.assets[0].wrapped_symbol,
                    apy=record.apy,
                    risk_profile=_get_risk_profile_for_single(record.assets[0].asset),
                )
            )
        elif len(record.assets) == 2:
            asset_pairs.append(
                AssetPair(
                    network=record.network,
                    protocol=record.protocol,
                    symbol_0=record.assets[0].asset,
                    symbol_0_wrapped=record.assets[0].wrapped_symbol,
                    symbol_1=record.assets[1].asset,
                    symbol_1_wrapped=record.assets[1].wrapped_symbol,
                    apy=record.apy,
                    risk_profile=_get_risk_profile_for_pair(
                        record.assets[0].asset, record.assets[1].asset
                    ),
                )
            )
    return assets, asset_pairs


@asgi_app.on_event("startup")
async def _init():
    await _update_state()
    asyncio.create_task(_update_state_loop())


async def _update_state():
    logger.info("updating state from ingest")
    assets, asset_pairs = await _update_ingest()
    combined: List[Union[AssetSingle, AssetPair]] = [*assets, *asset_pairs]
    # sort all by their apy
    assets.sort(key=lambda a: a.apy, reverse=True)
    asset_pairs.sort(key=lambda a: a.apy, reverse=True)
    combined.sort(key=lambda a: a.apy, reverse=True)

    asgi_app.state.assets = assets
    asgi_app.state.asset_pairs = asset_pairs
    asgi_app.state.combined = combined
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
