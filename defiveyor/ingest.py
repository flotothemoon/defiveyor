import asyncio
import logging
import os

import aiohttp

from defiveyor import utils

logger = logging.getLogger("ingest")

ZAPPER_API_KEY = os.environ["ZAPPER_API_KEY"]


async def _ingest_zapper(session: aiohttp.ClientSession):
    base_url = "https://api.zapper.fi/v1/"
    async with session.get(base_url + "pool-stats/supported", params={
        'api_key': ZAPPER_API_KEY
    }) as response:
        print("Status:", response.status)
        print("Content-type:", response.headers['content-type'])

        html = await response.text()
        print("Body:", html)


async def _ingest():
    logger.info("starting")
    async with aiohttp.ClientSession() as session:
        await _ingest_zapper(session)
    logger.info("completed")


if __name__ == '__main__':
    utils.configure_logging()
    asyncio.get_event_loop().run_until_complete(_ingest())
