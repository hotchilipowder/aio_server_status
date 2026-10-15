import pytest

from aio_server_status.probe import ProbeError, parse_probe

PROBE = """__AIO_HOST__
worker-1
__AIO_CPU_BEFORE__
cpu 100 0 100 800 0 0 0 0 0 0
__AIO_NET_BEFORE__
eth0: 1000 0 0 0 0 0 0 0 2000 0 0 0 0 0 0 0
lo: 100 0 0 0 0 0 0 0 100 0 0 0 0 0 0 0
__AIO_TIME_BEFORE__
100.00 0
__AIO_CPU_AFTER__
cpu 120 0 110 870 0 0 0 0 0 0
__AIO_NET_AFTER__
eth0: 3048 0 0 0 0 0 0 0 6096 0 0 0 0 0 0 0
lo: 900 0 0 0 0 0 0 0 900 0 0 0 0 0 0 0
__AIO_TIME_AFTER__
102.00 0
__AIO_MEM__
MemTotal: 8000000 kB
MemAvailable: 3000000 kB
SwapTotal: 2000000 kB
SwapFree: 1500000 kB
__AIO_LOAD__
0.10 0.20 0.30 1/100 42
__AIO_CORES__
4
__AIO_DISK__
Filesystem 1024-blocks Used Available Capacity Mounted on
/dev/sda1 100000 60000 40000 60% /
__AIO_GPU__
0, NVIDIA RTX 4090, 45, 1200, 24564, 55
__AIO_END__
"""


def test_parse_linux_metrics_and_network_rates():
    metrics = parse_probe(PROBE)
    assert metrics["cpu_percent"] == 30
    assert metrics["memory"]["percent"] == 62.5
    assert metrics["memory"]["total_bytes"] == 8000000 * 1024
    assert metrics["network"]["rx_bytes_per_second"] == 1024
    assert metrics["network"]["tx_bytes_per_second"] == 2048
    assert metrics["disks"][0]["mount"] == "/"
    assert metrics["gpus"][0]["name"] == "NVIDIA RTX 4090"
    assert metrics["cpu_count"] == 4
    assert metrics["uptime_seconds"] == 102


def test_gpu_optional_and_unsupported_fields_are_null():
    metrics = parse_probe(PROBE.replace("0, NVIDIA RTX 4090, 45, 1200, 24564, 55", ""))
    assert metrics["gpus"] == []
    metrics = parse_probe(PROBE.replace("45, 1200, 24564, 55", "[N/A], 1200, 24564, [Not Supported]"))
    assert metrics["gpus"][0]["utilization_percent"] is None


@pytest.mark.parametrize(
    "output", ["", "Linux only", PROBE.replace("__AIO_END__", ""), PROBE.replace("MemTotal: 8000000 kB", "")]
)
def test_reject_incomplete_probe(output):
    with pytest.raises(ProbeError):
        parse_probe(output)


def test_excludes_snap_squashfs_from_disk_usage():
    output = PROBE.replace(
        "__AIO_GPU__",
        "/dev/loop0 100 100 0 100% /snap/core22/1234\n"
        "__AIO_MOUNTS__\n/dev/sda1 / ext4 rw 0 0\n"
        "/dev/loop0 /snap/core22/1234 squashfs ro 0 0\n__AIO_GPU__",
    )
    metrics = parse_probe(output)
    assert [disk["mount"] for disk in metrics["disks"]] == ["/"]
