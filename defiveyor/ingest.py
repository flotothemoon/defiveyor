import asyncio
from itertools import chain
import logging
import os
from typing import List, Any, Mapping, Optional

import aiohttp
from attr import dataclass
import orjson

from defiveyor import utils
from defiveyor.supported import Protocol, Network, Asset
from defiveyor.utils import rate_limited

logger = logging.getLogger("ingest")

ZAPPER_API_KEY = os.environ["ZAPPER_API_KEY"]


@dataclass(frozen=True, slots=True, repr=False)
class WrappedAsset:
    asset: Asset
    wrapped_symbol: str

    def __str__(self):
        return repr(self)

    def __repr__(self) -> str:
        return f"WrappedAsset({self.asset.name},wrapped={self.wrapped_symbol})"

    @staticmethod
    def wrap(symbol: str) -> Optional["WrappedAsset"]:
        asset = Asset.map(symbol)
        if asset is None:
            return None
        else:
            return WrappedAsset(asset=asset, wrapped_symbol=symbol)


@dataclass(frozen=True, slots=True, repr=False)
class BasicRecord:
    network: Network
    protocol: Protocol
    assets: List[WrappedAsset]
    apy: float

    def __str__(self):
        return repr(self)

    def __repr__(self) -> str:
        assets_repr = [repr(asset) for asset in self.assets]
        return (
            f"BasicRecord("
            f"network={self.network.name},"
            f"protocol={self.protocol.name},"
            f"assets={assets_repr},"
            f"apy={self.apy}"
            f")"
        )


RecordList = List[BasicRecord]


async def _do_get(
    path: str,
    params: Mapping[str, Any],
    session: aiohttp.ClientSession,
    timeout_seconds=10,
):
    attempts = 0
    while True:
        logger.debug(f"GET {path}")
        try:
            async with session.get(
                path, params=params, timeout=timeout_seconds
            ) as response:
                response_text = await response.text()
                response_json = orjson.loads(response_text)
                return response_json
        except TimeoutError:
            attempts += 1
            retry_timeout_seconds = 2 ** (min(attempts, 5))
            logger.warning(
                f"request to {path} timed out,"
                f" retrying in {retry_timeout_seconds}s (attempt={attempts})"
            )
            await asyncio.sleep(retry_timeout_seconds)


async def _ingest_zapper(session: aiohttp.ClientSession) -> RecordList:
    # see https://docs.zapper.fi/zapper-api/api-guides
    base_url = "https://api.zapper.fi/v1/"

    @rate_limited(name="zapper", logger=logger, operations_per_second=1)
    async def _get(path: str, params: Mapping[str, Any] = None):
        params = params or {}
        params = {**params, "api_key": ZAPPER_API_KEY}
        final_path = base_url + path
        return await _do_get(final_path, params, session)

    async def _get_supported_pool_stats():
        return await _get("pool-stats/supported")

    async def _get_supported_vault_stats():
        return await _get("vault-stats/supported")

    async def _get_pool_stats(pool_type: str):
        return await _get(f"pool-stats/{pool_type}")

    async def _get_vault_stats(vault_type: str):
        return await _get(f"vault-stats/{vault_type}")

    async def _get_lending_stats(vault_type: str):
        return await _get(f"lending-stats/{vault_type}")

    protocols_mapping: Mapping[Protocol, str] = {
        # TODO @Feature @Data: bancor pool stats all have '0' as yearlyROI
        # Protocol.Bancor: 'bancor',
        # TODO @Feature @Data: Curve pools can have >2 tokens
        # Protocol.Curve: "curve",
        Protocol.OneInch: "1inch",
        Protocol.SushiSwap: "sushiswap",
        Protocol.UniSwap: "uniswap-v2",
        Protocol.Yearn: "yearn",
        Protocol.Aave: "aave",
        Protocol.Compound: "compound",
    }

    supported_pool_stats_by_network = await _get_supported_pool_stats()
    supported_pool_stats_by_network = {
        stats["network"]: stats["protocols"]
        for stats in supported_pool_stats_by_network
    }
    supported_vault_stats_by_network = await _get_supported_vault_stats()
    supported_vault_stats_by_network = {
        stats["network"]: stats["protocols"]
        for stats in supported_vault_stats_by_network
    }
    # there is no API endpoint for getting supported lending stats for some reason
    supported_lending_stats_by_network = {"ethereum": {"aave", "compound"}}

    records: RecordList = []
    for network in (Network.Ethereum,):
        network_key = network.value
        supported_pool_stats = supported_pool_stats_by_network.get(network_key)
        supported_vault_stats = supported_vault_stats_by_network.get(network_key)
        supported_lending_stats = supported_lending_stats_by_network.get(network_key)
        for protocol, protocol_key in protocols_mapping.items():
            if protocol_key in supported_pool_stats:
                pool_stats = await _get_pool_stats(protocol_key)
                for pool_stat in pool_stats:
                    assets = [
                        WrappedAsset.wrap(token["symbol"])
                        for token in pool_stat["tokens"]
                        if token["reserve"] > 0
                    ]
                    any_unknown = any([asset is None for asset in assets])
                    assets = [asset for asset in assets if asset is not None]
                    # TODO @Robustness: do something if any unknown?
                    if len(assets) != 2 or any_unknown:
                        continue

                    apy = pool_stat["yearlyROI"] or 0
                    if apy <= 0:
                        continue
                    records.append(
                        BasicRecord(
                            protocol=protocol,
                            network=network,
                            assets=assets,
                            apy=apy,
                        )
                    )

            if protocol_key in supported_vault_stats:
                # TODO @Feature: record vault stats
                pass

            if protocol_key in supported_lending_stats:
                lending_stats = await _get_lending_stats(protocol_key)
                for lending_stat in lending_stats:
                    asset = WrappedAsset.wrap(lending_stat["symbol"])
                    if asset is None:
                        continue
                    apy = lending_stat["supplyApy"]
                    if apy <= 0:
                        continue

                    records.append(
                        BasicRecord(
                            protocol=protocol, network=network, assets=[asset], apy=apy
                        )
                    )

    return records


async def _ingest_dydx(session: aiohttp.ClientSession) -> RecordList:
    # see https://docs.dydx.exchange/#get-markets
    base_url = "https://api.dydx.exchange/v1/"

    @rate_limited(name="dydx", logger=logger, operations_per_second=1)
    async def _get(path: str, params: Mapping[str, Any] = None):
        params = params or {}
        final_path = base_url + path
        return await _do_get(final_path, params, session)

    async def _get_markets():
        response = await _get("markets")
        return response['markets']

    records: RecordList = []
    markets = await _get_markets()
    for market in markets:
        asset = WrappedAsset.wrap(market['symbol'])
        if asset is None:
            continue
        apy = float(market.get('totalSupplyAPY', 0.0))
        if apy <= 0:
            continue
        records.append(BasicRecord(
            protocol=Protocol.dYdX,
            network=Network.Ethereum,
            assets=[asset],
            apy=apy
        ))

    return records


async def _ingest_bancor(session: aiohttp.ClientSession) -> RecordList:
    # see https://docs.bancor.network/rest-api/api-reference
    base_url = "https://api-v2.bancor.network/"

    @rate_limited(name="bancor", logger=logger, operations_per_second=1)
    async def _get(path: str, params: Mapping[str, Any] = None):
        params = params or {}
        final_path = base_url + path
        return await _do_get(final_path, params, session)

    async def _get_pools():
        response = await _get("pools")
        return response['data']

    records: RecordList = []
    pools = await _get_pools()
    for pool in pools:
        if pool['dlt_type'] != Network.Ethereum.value:
            continue
        assets = [
            WrappedAsset.wrap(reserve['symbol'])
            for reserve in pool['reserves']
        ]
        assets = [asset for asset in assets if asset is not None]
        if len(assets) < 1:
            continue

        # apy is fees_24h annualised divided by liquidity
        fees_24h = float(pool['fees_24h']['usd'])
        liquidity = float(pool['liquidity']['usd'])
        if liquidity <= 0:
            continue
        fees_annualised = 365.2425 * fees_24h
        apy = fees_annualised / liquidity
        records.append(BasicRecord(
            protocol=Protocol.Bancor,
            network=Network.Ethereum,
            assets=assets,
            apy=apy
        ))

    return records


async def ingest() -> RecordList:
    logger.info("starting")

    async with aiohttp.ClientSession() as session:
        ingests_tasks = [
            _ingest_bancor(session),
            _ingest_dydx(session),
            _ingest_zapper(session),
        ]
        ingest_results = await asyncio.gather(*ingests_tasks)
        logger.info("completed")
        return list(chain(*ingest_results))


if __name__ == "__main__":
    utils.configure_logging()
    records: RecordList = asyncio.get_event_loop().run_until_complete(ingest())
    logger.info(f"got {len(records)} records")
    for record in records:
        logger.info(f"got record: {record}")
