"""Enabled by scripts/ssh_smoke.sh on a disposable Linux CI runner."""

import getpass
import os

import pytest

from aio_server_status.config import Host
from aio_server_status.probe import parse_probe
from aio_server_status.ssh import collect

pytestmark = pytest.mark.skipif(not os.getenv("AIO_SSH_TEST_KEY"), reason="Requires temporary Linux sshd")


@pytest.mark.asyncio
async def test_real_ssh_linux_probe():
    host = Host(
        host="127.0.0.1",
        name="CI Linux",
        user=getpass.getuser(),
        port=int(os.environ["AIO_SSH_TEST_PORT"]),
        identity_file=os.environ["AIO_SSH_TEST_KEY"],
    )
    metrics = parse_probe(await collect(host, 15))
    assert metrics["cpu_count"] >= 1
    assert metrics["memory"]["total_bytes"] > 0
    assert 0 <= metrics["cpu_percent"] <= 100
    assert len(metrics["load"]) == 3
    assert metrics["network"]["rx_bytes_per_second"] >= 0
    assert metrics["disks"], "Linux fixture should have a mounted filesystem"
