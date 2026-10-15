import asyncio
from unittest.mock import AsyncMock, patch

import pytest
from test_probe import PROBE

from aio_server_status.config import load_config
from aio_server_status.monitor import Monitor
from aio_server_status.server import create_app
from aio_server_status.ssh import SSHError, collect, ssh_arguments


@pytest.fixture
def config(tmp_path):
    path = tmp_path / "servers.yaml"
    path.write_text("servers: [healthy, broken]\ninterval: 5\n")
    return load_config(path)


@pytest.mark.asyncio
async def test_host_failure_isolated_and_recovery(config):
    async def collector(host, timeout_seconds):
        if host.host == "broken":
            raise SSHError("Permission denied (publickey)")
        return PROBE

    monitor = Monitor(config, collector=collector)
    await monitor.poll()
    data = monitor.snapshot()
    assert [s["status"] for s in data["servers"]] == ["online", "offline"]
    assert data["servers"][1]["metrics"] is None
    assert "Permission denied" in data["servers"][1]["error"]
    monitor.collector = AsyncMock(return_value=PROBE)
    await monitor.poll()
    assert monitor.snapshot()["servers"][1]["status"] == "online"
    assert monitor.snapshot()["servers"][1]["error"] is None


@pytest.mark.asyncio
async def test_history_bounded_and_failed_sample_not_reused(config):
    monitor = Monitor(config, collector=AsyncMock(return_value=PROBE))
    for _ in range(65):
        await monitor.poll()
    assert len(monitor.snapshot()["servers"][0]["history"]) == 60
    monitor.collector = AsyncMock(side_effect=SSHError("offline"))
    await monitor.poll()
    host = monitor.snapshot()["servers"][0]
    assert host["metrics"] is None
    assert host["last_success_at"]
    assert host["history"][-1]["cpu_percent"] is None


@pytest.mark.asyncio
async def test_api_and_auth(aiohttp_client, config):
    monitor = Monitor(config, collector=AsyncMock(return_value=PROBE))
    await monitor.poll()
    client = await aiohttp_client(create_app(config, monitor=monitor, start_monitor=False, token="secret"))
    assert (await client.get("/api/status")).status == 401
    response = await client.get("/api/status", headers={"Authorization": "Bearer secret"})
    assert response.status == 200
    assert len((await response.json())["servers"]) == 2
    assert "identity_file" not in await response.text()
    assert (await client.get("/healthz")).status == 200
    assert (await client.get("/api/missing", headers={"Authorization": "Bearer secret"})).status == 404


def test_ssh_uses_batch_mode_and_strict_host_keys(config):
    args = ssh_arguments(config.servers[0], config.timeout)
    assert "BatchMode=yes" in args
    assert "StrictHostKeyChecking=yes" in args
    assert args[-3:] == ["healthy", "sh", "-s"]


@pytest.mark.asyncio
async def test_ssh_timeout_kills_process(config):
    process = AsyncMock()
    process.kill = lambda: None
    process.returncode = None
    process.communicate.side_effect = asyncio.TimeoutError
    with (
        patch("asyncio.create_subprocess_exec", return_value=process),
        patch("os.killpg") as kill_group,
    ):
        with pytest.raises(SSHError, match="timed out"):
            await collect(config.servers[0], 1)
    process.wait.assert_awaited_once()
    kill_group.assert_called_once()


@pytest.mark.asyncio
@pytest.mark.parametrize("cancel", [False, True])
async def test_real_descendant_processes_are_reaped(config, monkeypatch, cancel):
    import sys
    from time import monotonic

    from aio_server_status import ssh

    # The child inherits stdout/stderr, just like ProxyJump/ProxyCommand helpers.
    command = [
        sys.executable,
        "-c",
        "import subprocess,sys,time; "
        "subprocess.Popen([sys.executable, '-c', 'import time;time.sleep(4)']); time.sleep(4)",
    ]
    monkeypatch.setattr(ssh, "ssh_arguments", lambda host, timeout: command)
    started = monotonic()
    if cancel:
        task = asyncio.create_task(collect(config.servers[0], 10))
        await asyncio.sleep(0.15)
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
    else:
        with pytest.raises(SSHError, match="timed out"):
            await collect(config.servers[0], 0.15)
    assert monotonic() - started < 2, "Descendant pipes must not defeat the collection timeout"
