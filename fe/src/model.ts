export type Memory = {
  total_bytes: number;
  used_bytes: number;
  percent: number;
};
export type Disk = {
  filesystem: string;
  mount: string;
  total_bytes: number;
  used_bytes: number;
  available_bytes: number;
  percent: number;
};
export type GPU = {
  index: string;
  name: string;
  utilization_percent: number | null;
  memory_used_bytes: number | null;
  memory_total_bytes: number | null;
  temperature_celsius: number | null;
};
export type Metrics = {
  hostname: string;
  cpu_count: number;
  cpu_percent: number | null;
  memory: Memory;
  swap: Memory;
  load: number[];
  uptime_seconds: number;
  network: {
    rx_bytes_per_second: number | null;
    tx_bytes_per_second: number | null;
  };
  disks: Disk[];
  gpus: GPU[];
};
export type Server = {
  id: string;
  name: string;
  group: string;
  status: "online" | "offline" | "connecting";
  checked_at: string | null;
  last_success_at: string | null;
  latency_ms: number | null;
  error: string | null;
  metrics: Metrics | null;
  history: {
    at: string;
    cpu_percent: number | null;
    memory_percent: number | null;
  }[];
};
export type Snapshot = {
  title: string;
  generated_at: string;
  interval: number;
  servers: Server[];
};

export function formatBytes(value: number | null | undefined): string {
  if (value == null || !Number.isFinite(value)) return "—";
  if (value === 0) return "0 B";
  const units = ["B", "KB", "MB", "GB", "TB"];
  const index = Math.min(
    4,
    Math.max(0, Math.floor(Math.log(Math.abs(value)) / Math.log(1024))),
  );
  return `${(value / 1024 ** index).toFixed(index ? 1 : 0)} ${units[index]}`;
}
export const percent = (value: number | null | undefined) =>
  value == null ? "—" : `${value.toFixed(1)}%`;
export function isStale(
  at: string,
  interval: number,
  current = Date.now(),
): boolean {
  return (
    !Number.isFinite(Date.parse(at)) ||
    current - Date.parse(at) > Math.max(30, interval * 3) * 1000
  );
}
export function uptime(seconds: number): string {
  const days = Math.floor(seconds / 86400);
  const hours = Math.floor((seconds % 86400) / 3600);
  return days
    ? `${days} 天 ${hours} 小时`
    : `${hours} 小时 ${Math.floor((seconds % 3600) / 60)} 分钟`;
}
export function filterServers(
  servers: Server[],
  search: string,
  group: string,
  status: string,
): Server[] {
  const query = search.trim().toLocaleLowerCase();
  return servers.filter(
    (s) =>
      (group === "all" || s.group === group) &&
      (status === "all" || s.status === status) &&
      `${s.name} ${s.id} ${s.group} ${s.metrics?.hostname ?? ""}`
        .toLocaleLowerCase()
        .includes(query),
  );
}
