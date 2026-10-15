import type { Server, Snapshot } from "./model";

export function demoSnapshot(): Snapshot {
  const now = Date.now();
  const specs = [
    ["web-prod-01", "Production", 24.6, 42.1, 38, 8, 16, 320],
    ["web-prod-02", "Production", 18.2, 35.8, 46, 8, 16, 320],
    ["gpu-worker-01", "Compute", 62.4, 68.3, 54, 32, 128, 2048],
    ["db-primary", "Production", 38.7, 76.4, 67, 16, 64, 1024],
    ["edge-singapore", "Edge", 8.3, 23.6, 29, 4, 8, 160],
    ["backup-node", "Storage", 0, 0, 0, 4, 16, 4096],
  ] as const;
  const servers: Server[] = specs.map(
    ([name, group, cpu, memory, disk, cores, ram, storage], i) => {
      const offline = i === 5;
      return {
        id: name,
        name,
        group,
        status: offline ? "offline" : "online",
        checked_at: new Date(now).toISOString(),
        last_success_at: new Date(now - (offline ? 3600000 : 0)).toISOString(),
        latency_ms: offline ? 10000 : 1100 + i * 41,
        error: offline ? "SSH 连接超时，请检查网络和跳板机配置。" : null,
        metrics: offline
          ? null
          : {
              hostname: name,
              cpu_count: cores,
              cpu_percent: cpu,
              memory: {
                total_bytes: ram * 1024 ** 3,
                used_bytes: (ram * 1024 ** 3 * memory) / 100,
                percent: memory,
              },
              swap: { total_bytes: 2 * 1024 ** 3, used_bytes: 0, percent: 0 },
              load: [(cpu * cores) / 100, 0.8, 0.6],
              uptime_seconds: 86400 * (36 + i * 9) + 14000,
              network: {
                rx_bytes_per_second: (2.4 + i * 0.6) * 1024 ** 2,
                tx_bytes_per_second: (1.1 + i * 0.3) * 1024 ** 2,
              },
              disks: [
                {
                  filesystem: "/dev/sda1",
                  mount: "/",
                  total_bytes: storage * 1024 ** 3,
                  used_bytes: (storage * 1024 ** 3 * disk) / 100,
                  available_bytes: storage * 1024 ** 3 * (1 - disk / 100),
                  percent: disk,
                },
              ],
              gpus:
                i === 2
                  ? [
                      {
                        index: "0",
                        name: "NVIDIA RTX 4090",
                        utilization_percent: 84,
                        memory_used_bytes: 18.4 * 1024 ** 3,
                        memory_total_bytes: 24 * 1024 ** 3,
                        temperature_celsius: 64,
                      },
                    ]
                  : [],
            },
        history: Array.from({ length: 36 }, (_, n) => ({
          at: new Date(now - (35 - n) * 10000).toISOString(),
          cpu_percent: offline
            ? null
            : Math.max(
                2,
                cpu + Math.sin(n * 0.7 + i * 2) * 10 + Math.cos(n * 1.7) * 5,
              ),
          memory_percent: offline ? null : memory,
        })),
      };
    },
  );
  return {
    title: "My infrastructure",
    generated_at: new Date(now).toISOString(),
    interval: 10,
    servers,
  };
}
