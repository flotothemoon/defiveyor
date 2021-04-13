import asyncio
import logging
import os
from typing import List, Union, Any, Mapping

import aiohttp
import orjson

from defiveyor import utils, models
from defiveyor.crud import engine
from defiveyor.models import create_all
from defiveyor.supported import Protocol, Network, Asset
from defiveyor.utils import rate_limited

logger = logging.getLogger("ingest")

ZAPPER_API_KEY = os.environ["ZAPPER_API_KEY"]

Record = Union[models.AssetReturnRecord, models.AssetPairReturnRecord]
RecordList = List[Record]


async def _ingest_zapper(session: aiohttp.ClientSession) -> RecordList:
    records: RecordList = []

    base_url = "https://api.zapper.fi/v1/"

    @rate_limited(name="zapper", logger=logger, operations_per_second=1)
    async def _get(path: str, params: Mapping[str, Any] = None):
        params = params or {}
        final_path = base_url + path
        logger.debug(f"getting {final_path}")
        async with session.get(
            final_path, params={"api_key": ZAPPER_API_KEY, **params}
        ) as response:
            response_text = await response.text()
            response_json = orjson.loads(response_text)
            return response_json

    async def _get_supported_pool_stats():
        return await _get("pool-stats/supported")

    async def _get_supported_vault_stats():
        return await _get("vault-stats/supported")

    async def _get_supported_lending_stats():
        return await _get("lending-stats/supported")

    async def _get_pool_stats(pool_type: str):
        return await _get(f"pool-stats/{pool_type}")

    async def _get_vault_stats(vault_type: str):
        return await _get(f"vault-stats/{vault_type}")

    async def _get_lending_stats(vault_type: str):
        return await _get(f"lending-stats/{vault_type}")

    protocols_mapping: Mapping[Protocol, str] = {
        # TODO @Feature @Data: bancor pool stats all have '0' as yearlyROI
        # Protocol.Bancor: 'bancor',
        Protocol.Curve: "curve",
        Protocol.OneInch: "1inch",
        Protocol.SushiSwap: "sushiswap",
        Protocol.UniSwap: "uniswap-v2",
        Protocol.Yearn: "yearn",
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
    supported_lending_stats_by_network = await _get_supported_lending_stats()
    supported_lending_stats_by_network = {
        stats["network"]: stats["protocols"]
        for stats in supported_lending_stats_by_network
    }

    for network in (Network.Ethereum,):
        network_key = network.value
        supported_pool_stats = supported_pool_stats_by_network.get(network_key)
        supported_vault_stats = supported_vault_stats_by_network.get(network_key)
        supported_lending_stats = supported_lending_stats_by_network.get(network_key)
        for protocol, protocol_key in protocols_mapping.items():
            if protocol_key in supported_pool_stats:
                pool_stats = await _get_pool_stats(protocol_key)
                for pool_stat in pool_stats:
                    assets = {
                        Asset.map(token["symbol"])
                        for token in pool_stat["tokens"]
                        if token["reserve"] > 0
                    }
                    any_unknown = any([asset is None for asset in assets])
                    # TODO @Robustness: do something if any unknown?
                    assets = [asset for asset in assets if asset is not None]
                    if len(assets) > 2:
                        logger.warning(f"ignoring pool with >2 assets: {assets}")
                        continue
                    apy = pool_stat['yearlyROI']

                    records.append(models.AssetPairReturnRecord(

                    ))

            if protocol_key in supported_vault_stats:
                vault_stats = await _get_vault_stats(protocol_key)

    return records


async def _ingest_compound(session: aiohttp.ClientSession) -> RecordList:
    records: RecordList = []
    return records


async def _ingest() -> RecordList:
    logger.info("starting")

    records = []
    async with aiohttp.ClientSession() as session:
        records.extend(await _ingest_zapper(session))

    logger.info("completed")

    return records


if __name__ == "__main__":
    utils.configure_logging()
    create_all(engine)
    asyncio.get_event_loop().run_until_complete(_ingest())
