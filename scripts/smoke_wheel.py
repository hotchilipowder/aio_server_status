"""Run outside the source tree after installing the built wheel."""

import asyncio
from importlib.resources import files

from aiohttp.test_utils import TestClient, TestServer

from aio_server_status.config import Config, Host
from aio_server_status.server import create_app


async def main():
    static = files("aio_server_status").joinpath("static")
    assert static.joinpath("index.html").is_file(), "Wheel is missing the dashboard"
    assert files("aio_server_status").joinpath("probe.sh").is_file(), "Wheel is missing the SSH probe"
    config = Config(servers=(Host(host="example", name="example"),))
    async with TestClient(TestServer(create_app(config, start_monitor=False))) as client:
        response = await client.get("/")
        assert response.status == 200
        assert '<div id="root">' in await response.text()
        for asset in static.joinpath("assets").iterdir():
            response = await client.get(f"/assets/{asset.name}")
            assert response.status == 200, f"Missing asset {asset.name}"
        assert (await client.get("/api/status")).status == 200
    print("Installed wheel serves the dashboard, assets and API.")


asyncio.run(main())
