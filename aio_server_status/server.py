"""HTTP API and the bundled static dashboard on a single local port."""

import asyncio
import hmac
from contextlib import suppress
from importlib.resources import files

from aiohttp import web

from .config import Config
from .monitor import Monitor


def create_app(config: Config, *, monitor=None, start_monitor=True, token=None) -> web.Application:
    monitor = monitor or Monitor(config)

    @web.middleware
    async def headers_and_auth(request, handler):
        if request.path.startswith("/api/") and token:
            actual = request.headers.get("Authorization", "").encode()
            if not hmac.compare_digest(actual, f"Bearer {token}".encode()):
                return web.json_response({"error": "A valid access token is required"}, status=401)
        response = await handler(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "same-origin"
        if request.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store"
        return response

    app = web.Application(middlewares=[headers_and_auth])

    async def status(request):
        return web.json_response(monitor.snapshot())

    async def health(request):
        return web.json_response({"status": "ok"})

    static = files("aio_server_status").joinpath("static")

    async def index(request):
        path = static.joinpath("index.html")
        if not path.is_file():
            return web.Response(
                text="Dashboard is not built. Run npm ci and npm run build in fe/, then "
                "python scripts/bundle_frontend.py from the project root. API: /api/status",
                status=503,
            )
        return web.FileResponse(path)

    app.router.add_get("/api/status", status)
    app.router.add_get("/healthz", health)
    app.router.add_get("/", index)
    assets = static.joinpath("assets")
    if assets.is_dir():
        app.router.add_static("/assets/", assets, show_index=False)

    async def lifecycle(app):
        task = asyncio.create_task(monitor.run())
        yield
        task.cancel()
        with suppress(asyncio.CancelledError):
            await task

    if start_monitor:
        app.cleanup_ctx.append(lifecycle)
    return app
