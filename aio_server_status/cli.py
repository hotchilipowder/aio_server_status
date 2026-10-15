"""Minimal setup and launch commands."""

import argparse
import asyncio
import logging
import os
from pathlib import Path

from aiohttp import web

from . import __version__
from .config import ConfigError, load_config
from .monitor import Monitor
from .server import create_app

TEMPLATE = """# SSH aliases from ~/.ssh/config. Verify with: ssh my-server
servers:
  - my-server
# interval: 10
# timeout: 10
# concurrency: 10
# listen: 127.0.0.1
# port: 8080
"""


async def _check(config):
    monitor = Monitor(config)
    await monitor.poll()
    for server in monitor.snapshot()["servers"]:
        detail = server["error"] or f"{server['metrics']['cpu_count']} CPUs, probe OK"
        print(f"{server['status'].upper():7} {server['name']}: {detail}")
    return 0 if all(s["status"] == "online" for s in monitor.snapshot()["servers"]) else 1


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Agentless Linux monitoring over your existing SSH connections"
    )
    parser.add_argument("--version", action="version", version=__version__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    for command, help_text in [
        ("init", "Create a minimal configuration"),
        ("check", "Verify every SSH connection and metric probe"),
        ("serve", "Start the dashboard and background collector"),
    ]:
        subparser = subparsers.add_parser(command, help=help_text)
        subparser.add_argument("--config", default="servers.yaml", help="YAML configuration path")
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    try:
        if args.command == "init":
            path = Path(args.config).expanduser()
            try:
                with path.open("x", encoding="utf-8") as stream:
                    stream.write(TEMPLATE)
            except FileExistsError:
                raise ConfigError(f"{path} already exists; edit it or choose --config another.yaml") from None
            print(f"Created {path}. Add SSH aliases, then run aio-server-status check and serve.")
            return 0
        config = load_config(args.config)
        if args.command == "check":
            return asyncio.run(_check(config))
        token = os.environ.get("AIO_STATUS_TOKEN") or None
        web.run_app(create_app(config, token=token), host=config.listen, port=config.port, access_log=None)
        return 0
    except (ConfigError, OSError) as exc:
        parser.exit(2, f"Error: {exc}\n")


if __name__ == "__main__":
    raise SystemExit(main())
