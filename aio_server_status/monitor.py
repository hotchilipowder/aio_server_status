"""Bounded concurrent polling and a small in-memory history."""

import asyncio
import copy
import logging
from collections import deque
from datetime import UTC, datetime
from time import monotonic

from .config import Config
from .probe import ProbeError, parse_probe
from .ssh import SSHError, collect

logger = logging.getLogger(__name__)


def now():
    return datetime.now(UTC).isoformat()


class Monitor:
    def __init__(self, config: Config, collector=collect):
        self.config = config
        self.collector = collector
        self.generated_at = now()
        self._semaphore = asyncio.Semaphore(config.concurrency)
        self.states = {
            host.host: {
                "id": host.host,
                "name": host.name,
                "group": host.group,
                "status": "connecting",
                "checked_at": None,
                "last_success_at": None,
                "latency_ms": None,
                "error": None,
                "metrics": None,
                "history": deque(maxlen=60),
            }
            for host in config.servers
        }

    async def _poll_host(self, host):
        async with self._semaphore:
            started = monotonic()
            state = self.states[host.host]
            try:
                output = await self.collector(host, self.config.timeout)
                metrics = parse_probe(output)
            except (SSHError, ProbeError) as exc:
                state.update(status="offline", error=str(exc), metrics=None)
            else:
                state.update(status="online", error=None, metrics=metrics, last_success_at=now())
            state["checked_at"] = now()
            state["latency_ms"] = round((monotonic() - started) * 1000)
            metrics = state["metrics"]
            state["history"].append(
                {
                    "at": state["checked_at"],
                    "cpu_percent": metrics["cpu_percent"] if metrics else None,
                    "memory_percent": metrics["memory"]["percent"] if metrics else None,
                }
            )

    async def poll(self):
        await asyncio.gather(*(self._poll_host(host) for host in self.config.servers))
        self.generated_at = now()

    async def run(self):
        while True:
            started = monotonic()
            try:
                await self.poll()
            except Exception:
                logger.exception("Unexpected polling failure")
            await asyncio.sleep(max(0.1, self.config.interval - (monotonic() - started)))

    def snapshot(self):
        servers = []
        for state in self.states.values():
            servers.append({**state, "history": list(state["history"])})
        return copy.deepcopy(
            {
                "title": self.config.title,
                "generated_at": self.generated_at,
                "interval": self.config.interval,
                "servers": servers,
            }
        )
