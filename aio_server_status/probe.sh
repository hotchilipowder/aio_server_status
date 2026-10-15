#!/bin/sh
# Fixed, read-only probe. No remote Python, root privileges or installed agent.
set -eu
export LC_ALL=C
if [ ! -r /proc/stat ] || [ ! -r /proc/meminfo ]; then
    echo 'AIO requires a Linux target with readable /proc.' >&2
    exit 1
fi
printf '__AIO_HOST__\n'
hostname
printf '__AIO_CPU_BEFORE__\n'
head -n 1 /proc/stat
printf '__AIO_NET_BEFORE__\n'
cat /proc/net/dev
printf '__AIO_TIME_BEFORE__\n'
cat /proc/uptime
sleep 1
printf '__AIO_CPU_AFTER__\n'
head -n 1 /proc/stat
printf '__AIO_NET_AFTER__\n'
cat /proc/net/dev
printf '__AIO_TIME_AFTER__\n'
cat /proc/uptime
printf '__AIO_MEM__\n'
cat /proc/meminfo
printf '__AIO_LOAD__\n'
cat /proc/loadavg
printf '__AIO_CORES__\n'
awk '/^cpu[0-9]+ / {n++} END {print n+0}' /proc/stat
printf '__AIO_DISK__\n'
df -Pk | awk 'NR == 1 || ($1 !~ /^(tmpfs|devtmpfs|udev|shm|overlay|none)$/ && $6 !~ /^\/(proc|sys|dev)(\/|$)/)'
printf '__AIO_MOUNTS__\n'
cat /proc/mounts
printf '__AIO_GPU__\n'
if command -v nvidia-smi >/dev/null 2>&1; then
    nvidia-smi --query-gpu=index,name,utilization.gpu,memory.used,memory.total,temperature.gpu --format=csv,noheader,nounits 2>/dev/null || true
fi
printf '__AIO_END__\n'
