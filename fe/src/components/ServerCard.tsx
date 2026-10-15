import {
  ArrowDown,
  ArrowUp,
  ChevronDown,
  Cpu,
  Server as ServerIcon,
  WifiOff,
} from "lucide-react";
import type { Server } from "../model";
import { formatBytes, isStale, percent, uptime } from "../model";

const statusLabels = { online: "在线", offline: "离线", connecting: "连接中" };

function Sparkline({ history }: { history: Server["history"] }) {
  const segments: string[] = [];
  let current: string[] = [];
  history.forEach((sample, i) => {
    if (sample.cpu_percent == null) {
      if (current.length) segments.push(current.join(" "));
      current = [];
    } else {
      current.push(
        `${(i * 300) / Math.max(1, history.length - 1)},${48 - sample.cpu_percent * 0.44}`,
      );
    }
  });
  if (current.length) segments.push(current.join(" "));
  return (
    <svg
      className="sparkline"
      viewBox="0 0 300 52"
      preserveAspectRatio="none"
      role="img"
      aria-label="最近采样的 CPU 使用率趋势"
    >
      <path
        d="M0 50H300 M0 25H300"
        stroke="currentColor"
        strokeOpacity="0.08"
        fill="none"
      />
      {segments.map((points, i) => (
        <polyline
          key={i}
          points={points}
          fill="none"
          stroke="currentColor"
          strokeWidth="1.8"
          strokeLinecap="round"
          strokeLinejoin="round"
          vectorEffect="non-scaling-stroke"
        />
      ))}
    </svg>
  );
}

function Meter({
  label,
  value,
  detail,
}: {
  label: string;
  value: number | null;
  detail: string;
}) {
  return (
    <div className={`meter ${value != null && value >= 85 ? "high" : ""}`}>
      <div className="meter-heading">
        <span>{label}</span>
        <strong>{percent(value)}</strong>
      </div>
      <div className="meter-track">
        <i style={{ width: `${Math.max(0, Math.min(100, value ?? 0))}%` }} />
      </div>
      <div className="meter-detail">{detail}</div>
    </div>
  );
}

export function ServerCard({
  server,
  interval,
  clock,
}: {
  server: Server;
  interval: number;
  clock: number;
}) {
  const m = server.metrics;
  const stale =
    !!server.checked_at && isStale(server.checked_at, interval, clock);
  const disk = m?.disks.reduce<(typeof m.disks)[number] | undefined>(
    (worst, item) => (!worst || item.percent > worst.percent ? item : worst),
    undefined,
  );
  return (
    <article className={`server-card ${server.status} ${stale ? "stale" : ""}`}>
      <div className="card-top">
        <div className="server-symbol">
          <ServerIcon size={19} />
        </div>
        <span className={`status ${server.status}`}>
          <i />
          {stale ? "数据过期" : statusLabels[server.status]}
        </span>
      </div>
      <div className="server-title">
        <h3>{server.name}</h3>
        <span className="group-label">{server.group}</span>
      </div>
      <div className="host-subtitle">
        {m ? `${m.cpu_count} vCPU` : "SSH"}
        <span>·</span>
        {m ? `${formatBytes(m.memory.total_bytes)} RAM` : server.id}
      </div>
      {m ? (
        <>
          <div className="meters">
            <Meter
              label="CPU"
              value={m.cpu_percent}
              detail={`${m.cpu_count} 个逻辑核心`}
            />
            <Meter
              label="内存"
              value={m.memory.percent}
              detail={`${formatBytes(m.memory.used_bytes)} / ${formatBytes(m.memory.total_bytes)}`}
            />
            <Meter
              label="磁盘"
              value={disk?.percent ?? null}
              detail={
                disk
                  ? `${formatBytes(disk.used_bytes)} / ${formatBytes(disk.total_bytes)}`
                  : "暂无挂载点"
              }
            />
          </div>
          <div className="chart-caption">
            <span>CPU 趋势</span>
            <span>最近 {server.history.length} 次采样</span>
          </div>
          <Sparkline history={server.history} />
          {m.gpus.length > 0 && (
            <div className="gpu-strip">
              <Cpu size={14} />
              <span>{m.gpus[0].name}</span>
              <strong>{percent(m.gpus[0].utilization_percent)}</strong>
            </div>
          )}
          <div className="network-row">
            <span>
              <ArrowDown size={13} />
              {formatBytes(m.network.rx_bytes_per_second)}/s
            </span>
            <span>
              <ArrowUp size={13} />
              {formatBytes(m.network.tx_bytes_per_second)}/s
            </span>
          </div>
          <details className="server-details">
            <summary>
              <span>
                <span className="uptime-dot" />
                已运行 {uptime(m.uptime_seconds)}
              </span>
              <span>
                详情 <ChevronDown size={12} />
              </span>
            </summary>
            <div className="detail-content">
              <p>
                <span>主机名</span>
                <b>{m.hostname}</b>
              </p>
              <p>
                <span>负载 1 / 5 / 15m</span>
                <b>{m.load.map((v) => v.toFixed(2)).join(" / ")}</b>
              </p>
              <p>
                <span>Swap</span>
                <b>
                  {formatBytes(m.swap.used_bytes)} /{" "}
                  {formatBytes(m.swap.total_bytes)}
                </b>
              </p>
              {m.disks.map((d) => (
                <p key={`${d.filesystem}:${d.mount}`}>
                  <span>磁盘 {d.mount}</span>
                  <b>
                    {percent(d.percent)} · {formatBytes(d.available_bytes)} 可用
                  </b>
                </p>
              ))}
              {m.gpus.map((g) => (
                <p key={g.index}>
                  <span>
                    GPU {g.index} · {g.name}
                  </span>
                  <b>
                    {percent(g.utilization_percent)} ·{" "}
                    {g.temperature_celsius ?? "—"} °C ·{" "}
                    {formatBytes(g.memory_used_bytes)} /{" "}
                    {formatBytes(g.memory_total_bytes)}
                  </b>
                </p>
              ))}
              <p>
                <span>采集耗时</span>
                <b>{server.latency_ms} ms（含采样等待）</b>
              </p>
              <p>
                <span>最后采集</span>
                <b>
                  {server.checked_at
                    ? new Date(server.checked_at).toLocaleString()
                    : "—"}
                </b>
              </p>
            </div>
          </details>
        </>
      ) : (
        <div className="offline-content">
          <WifiOff size={28} />
          <strong>
            {server.status === "connecting"
              ? "正在建立 SSH 连接"
              : "暂时无法连接"}
          </strong>
          <p>{server.error ?? "首次采集正在进行，请稍候。"}</p>
          <div className="retry-label">每 {interval} 秒自动重试</div>
          {server.last_success_at && (
            <small>
              上次在线 {new Date(server.last_success_at).toLocaleString()}
            </small>
          )}
        </div>
      )}
    </article>
  );
}
