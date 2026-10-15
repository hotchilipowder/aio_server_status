"""Parse the probe's sectioned text protocol into JSON-safe metrics."""

import csv
import math
import re


class ProbeError(ValueError):
    """Incomplete or unsupported probe output."""


def _cpu(text):
    values = [int(n) for n in text.split()[1:9]]
    return sum(values), sum(values[3:5])


def _network(text):
    rx = tx = 0
    for line in text.splitlines():
        if ":" not in line:
            continue
        name, values = line.rsplit(":", 1)
        if name.strip() == "lo":
            continue
        fields = values.split()
        rx += int(fields[0])
        tx += int(fields[8])
    return rx, tx


def _optional_number(value):
    try:
        number = float(value)
        return number if math.isfinite(number) else None
    except ValueError:
        return None


def _memory(total, available):
    used = max(0, total - available)
    return {"total_bytes": total, "used_bytes": used, "percent": round(used / total * 100, 1) if total else 0}


def parse_probe(output: str) -> dict:
    try:
        parts = re.split(r"^__AIO_(\w+)__\s*$", output, flags=re.MULTILINE)
        sections = {parts[i]: parts[i + 1].strip() for i in range(1, len(parts) - 1, 2)}
        required = {
            "HOST",
            "CPU_BEFORE",
            "CPU_AFTER",
            "NET_BEFORE",
            "NET_AFTER",
            "TIME_BEFORE",
            "TIME_AFTER",
            "MEM",
            "LOAD",
            "CORES",
            "DISK",
            "GPU",
            "END",
        }
        if not required <= sections.keys():
            raise ValueError("missing sections; target must be Linux")
        mem = {}
        for line in sections["MEM"].splitlines():
            key, value = line.split(":", 1)
            mem[key] = int(value.split()[0]) * 1024
        if mem["MemTotal"] <= 0:
            raise ValueError("invalid memory total")
        before, idle_before = _cpu(sections["CPU_BEFORE"])
        after, idle_after = _cpu(sections["CPU_AFTER"])
        delta = after - before
        cpu = (
            round(max(0, min(100, (1 - (idle_after - idle_before) / delta) * 100)), 1) if delta > 0 else None
        )
        elapsed = float(sections["TIME_AFTER"].split()[0]) - float(sections["TIME_BEFORE"].split()[0])
        rx1, tx1 = _network(sections["NET_BEFORE"])
        rx2, tx2 = _network(sections["NET_AFTER"])
        # Snap images are squashfs and always report 100% in df. They are not
        # writable storage and must not become the dashboard's fullest disk.
        excluded_mounts = set()
        for line in sections.get("MOUNTS", "").splitlines():
            mount = line.split()
            if len(mount) >= 3 and mount[2] in {"squashfs", "tmpfs", "devtmpfs", "overlay"}:
                excluded_mounts.add(mount[1].replace(r"\040", " ").replace(r"\011", "\t"))
        disks = []
        for line in sections["DISK"].splitlines()[1:]:
            fields = line.split(None, 5)
            if len(fields) == 6 and fields[4].endswith("%") and fields[5] not in excluded_mounts:
                disks.append(
                    {
                        "filesystem": fields[0],
                        "total_bytes": int(fields[1]) * 1024,
                        "used_bytes": int(fields[2]) * 1024,
                        "available_bytes": int(fields[3]) * 1024,
                        "percent": float(fields[4][:-1]),
                        "mount": fields[5],
                    }
                )
        gpus = []
        for row in csv.reader(sections["GPU"].splitlines(), skipinitialspace=True):
            if len(row) != 6:
                continue
            used, total = _optional_number(row[3]), _optional_number(row[4])
            gpus.append(
                {
                    "index": row[0],
                    "name": row[1],
                    "utilization_percent": _optional_number(row[2]),
                    "memory_used_bytes": used * 1024**2 if used is not None else None,
                    "memory_total_bytes": total * 1024**2 if total is not None else None,
                    "temperature_celsius": _optional_number(row[5]),
                }
            )
        return {
            "hostname": sections["HOST"],
            "cpu_count": int(sections["CORES"]),
            "cpu_percent": cpu,
            "memory": _memory(mem["MemTotal"], mem["MemAvailable"]),
            "swap": _memory(mem.get("SwapTotal", 0), mem.get("SwapFree", 0)),
            "load": [float(v) for v in sections["LOAD"].split()[:3]],
            "uptime_seconds": float(sections["TIME_AFTER"].split()[0]),
            "network": {
                "rx_bytes_per_second": max(0, rx2 - rx1) / elapsed if elapsed > 0 else None,
                "tx_bytes_per_second": max(0, tx2 - tx1) / elapsed if elapsed > 0 else None,
            },
            "disks": disks,
            "gpus": gpus,
        }
    except (KeyError, ValueError, IndexError, ZeroDivisionError) as exc:
        raise ProbeError(f"Invalid Linux probe output: {exc}") from exc
