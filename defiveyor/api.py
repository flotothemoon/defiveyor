import os

import fastapi

asgi_app = fastapi.FastAPI(
    title="Defiveyor API", version="2021.4", openapi_url=None
)


@asgi_app.get("/assets")
async def get_assets():
    return []


@asgi_app.get("/pairs")
async def get_assets():
    return []
