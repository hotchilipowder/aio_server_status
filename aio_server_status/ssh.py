"""OpenSSH transport, preserving user configuration and host key verification."""

import asyncio
import math
import os
import signal
from contextlib import suppress
from importlib.resources import files

from .config import Host


class SSHError(RuntimeError):
    """An actionable SSH connection or probe failure."""


def ssh_arguments(host: Host, timeout: float) -> list[str]:
    args = [
        "ssh",
        "-T",
        "-o",
        "BatchMode=yes",
        "-o",
        "StrictHostKeyChecking=yes",
        "-o",
        f"ConnectTimeout={max(1, math.ceil(timeout))}",
        "-o",
        "ServerAliveInterval=5",
        "-o",
        "ServerAliveCountMax=1",
        "-o",
        "LogLevel=ERROR",
    ]
    if host.port:
        args.extend(["-p", str(host.port)])
    if host.user:
        args.extend(["-l", host.user])
    if host.identity_file:
        args.extend(["-i", host.identity_file])
    return [*args, "--", host.host, "sh", "-s"]


async def collect(host: Host, timeout_seconds: float) -> str:
    try:
        process = await asyncio.create_subprocess_exec(
            *ssh_arguments(host, timeout_seconds),
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            start_new_session=True,
        )
    except OSError as exc:
        raise SSHError(f"Cannot start OpenSSH: {exc.strerror}. Install the ssh client.") from exc
    try:
        script = files("aio_server_status").joinpath("probe.sh").read_bytes()
        stdout, stderr = await asyncio.wait_for(process.communicate(script), timeout=timeout_seconds)
    except (TimeoutError, asyncio.CancelledError) as exc:
        # Jump hosts and ProxyCommand helpers inherit the pipes. Killing only
        # ssh leaves communicate/wait blocked until those helpers exit.
        with suppress(ProcessLookupError):
            os.killpg(process.pid, signal.SIGKILL)
        with suppress(TimeoutError):
            await asyncio.wait_for(process.wait(), timeout=1)
        if isinstance(exc, asyncio.CancelledError):
            raise
        raise SSHError(
            f"SSH collection timed out after {timeout_seconds:g}s; check network and ProxyJump."
        ) from exc
    if process.returncode:
        detail = stderr.decode("utf-8", errors="replace").strip()[-500:]
        raise SSHError(detail or f"Remote probe exited with code {process.returncode}")
    return stdout.decode("utf-8", errors="replace")
