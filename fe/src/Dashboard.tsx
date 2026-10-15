import { useEffect, useState } from "react";
import {
  Activity,
  ArrowUpRight,
  Box,
  ChevronRight,
  Cpu,
  LayoutGrid,
  List,
  MemoryStick,
  Network,
  Radio,
  RefreshCw,
  Search,
  Server as ServerIcon,
  ShieldCheck,
  Terminal,
  WifiOff,
} from "lucide-react";
import type { Snapshot } from "./model";
import { filterServers, formatBytes, isStale } from "./model";

import { DOCS_URL as docs } from "./links";
import { ServerCard } from "./components/ServerCard";
import { Sidebar } from "./components/Sidebar";
export function Dashboard({
  snapshot,
  demo = false,
  error,
  onRefresh,
  refreshing = false,
}: {
  snapshot: Snapshot;
  demo?: boolean;
  error?: string | null;
  onRefresh?: () => void;
  refreshing?: boolean;
}) {
  const [search, setSearch] = useState("");
  const [group, setGroup] = useState("all");
  const [status, setStatus] = useState("all");
  const [view, setView] = useState("grid");
  const [clock, setClock] = useState(Date.now());
  useEffect(() => {
    const id = setInterval(() => setClock(Date.now()), 1000);
    return () => clearInterval(id);
  }, []);
  const servers = snapshot.servers;
  const online = servers.filter((s) => s.status === "online");
  const offline = servers.filter((s) => s.status === "offline").length;
  const groups = [...new Set(servers.map((s) => s.group))];
  const visible = filterServers(servers, search, group, status);
  const cpuValues = online.flatMap((s) =>
    s.metrics?.cpu_percent == null ? [] : [s.metrics.cpu_percent],
  );
  const avgCpu = cpuValues.length
    ? cpuValues.reduce((a, b) => a + b, 0) / cpuValues.length
    : null;
  const totalMemory = online.reduce(
    (sum, s) => sum + (s.metrics?.memory.total_bytes ?? 0),
    0,
  );
  const usedMemory = online.reduce(
    (sum, s) => sum + (s.metrics?.memory.used_bytes ?? 0),
    0,
  );
  const stale =
    isStale(snapshot.generated_at, snapshot.interval, clock) ||
    servers.some(
      (s) => s.checked_at && isStale(s.checked_at, snapshot.interval, clock),
    );
  return (
    <div className="app-shell">
      <Sidebar
        snapshot={snapshot}
        group={group}
        onGroupChange={setGroup}
        onReset={() => {
          setGroup("all");
          setStatus("all");
          setSearch("");
        }}
      />
      <div className="main-shell">
        <header className="topbar">
          <div>
            <span className="breadcrumb">工作空间</span>
            <ChevronRight size={13} />
            <span>基础设施总览</span>
          </div>
          <span className="transport">
            <Terminal size={13} />
            SSH / AGENTLESS
          </span>
        </header>
        <main>
          {demo && (
            <div className="demo-banner">
              <Radio size={15} />
              <span>演示模式 · 以下为模拟数据，未连接真实服务器。</span>
              <a href={`${docs}getting-started.html`}>
                连接我的服务器 <ArrowUpRight size={13} />
              </a>
            </div>
          )}
          <div className="page-heading">
            <div>
              <div className="eyebrow">INFRASTRUCTURE OVERVIEW</div>
              <h1>
                服务器总览<span className="heading-dot">.</span>
              </h1>
              <p>每一次心跳，尽在掌握。通过 SSH，轻松连接你的基础设施。</p>
            </div>
            <button
              className="refresh-button"
              disabled={refreshing || !onRefresh}
              onClick={onRefresh}
            >
              <RefreshCw size={14} className={refreshing ? "spinning" : ""} />
              刷新状态
            </button>
          </div>
          {(error || stale) && (
            <div className="error-banner" role="alert">
              <WifiOff size={16} />
              {error ?? "采集数据已过期，请检查控制机上的服务。"}{" "}
              {stale && "当前显示上次采样结果。"}
            </div>
          )}
          <section className="summary-grid" aria-label="资源概况">
            <div className="summary-card">
              <div>
                服务器总数
                <ServerIcon size={16} />
              </div>
              <strong>
                {servers.length}
                <span>台服务器</span>
              </strong>
              <small>
                <span className="green-text">{online.length} 在线</span>
                <span className="summary-divider" />
                {offline} 离线
              </small>
            </div>
            <div className="summary-card">
              <div>
                平均 CPU 使用率
                <Cpu size={17} />
              </div>
              <strong>
                {avgCpu == null ? "—" : avgCpu.toFixed(1)}
                <span>{avgCpu == null ? "" : "%"}</span>
              </strong>
              <small>
                <span className="mini-line" />
                {cpuValues.length} 台在线主机的平均值
              </small>
            </div>
            <div className="summary-card">
              <div>
                内存使用量
                <MemoryStick size={17} />
              </div>
              <strong>
                {online.length ? formatBytes(usedMemory).split(" ")[0] : "—"}
                <span>
                  {online.length ? formatBytes(usedMemory).split(" ")[1] : ""}
                  <em>/ {formatBytes(totalMemory)}</em>
                </span>
              </strong>
              <small>
                <span className="mini-memory">
                  <i
                    style={{
                      width: `${totalMemory ? (usedMemory / totalMemory) * 100 : 0}%`,
                    }}
                  />
                </span>
                {totalMemory
                  ? ((usedMemory / totalMemory) * 100).toFixed(1)
                  : "—"}
                % 已使用
              </small>
            </div>
            <div className="summary-card">
              <div>
                采集间隔
                <Radio size={17} />
              </div>
              <strong>
                {snapshot.interval}
                <span>秒</span>
              </strong>
              <small>
                <span className="tiny-dot" />
                SSH 自动采集 · 无需安装 Agent
              </small>
            </div>
          </section>
          <div
            className={`health-strip ${offline || stale ? "attention" : ""}`}
          >
            <div className="health-icon">
              <Activity size={19} />
            </div>
            <div>
              <strong>
                {stale
                  ? "部分采集数据需要更新"
                  : offline
                    ? `${online.length} 台服务器运行正常，${offline} 台需要关注`
                    : online.length === servers.length
                      ? "所有服务器运行正常"
                      : "正在连接服务器"}
              </strong>
              <span>
                {demo ? "当前为演示工作空间" : "采集连接已启用严格主机指纹校验"}
              </span>
            </div>
            <div className="last-updated">
              <i />
              <span>
                {demo
                  ? "模拟数据"
                  : `${Math.max(0, Math.floor((clock - Date.parse(snapshot.generated_at)) / 1000))} 秒前更新`}
              </span>
            </div>
          </div>
          <section className="servers-section" aria-label="服务器列表">
            <div className="section-title">
              <h2>
                我的服务器 <span>{visible.length}</span>
              </h2>
              <div className="section-tools">
                <label className="search">
                  <Search size={15} />
                  <input
                    type="search"
                    placeholder="搜索服务器…"
                    aria-label="搜索服务器"
                    value={search}
                    onChange={(e) => setSearch(e.target.value)}
                  />
                  <span className="search-hint">搜索</span>
                </label>
                <select
                  aria-label="筛选连接状态"
                  value={status}
                  onChange={(e) => setStatus(e.target.value)}
                >
                  <option value="all">全部状态</option>
                  <option value="online">在线</option>
                  <option value="offline">离线</option>
                  <option value="connecting">连接中</option>
                </select>
                <div className="view-switch">
                  <button
                    aria-label="网格视图"
                    aria-pressed={view === "grid"}
                    className={view === "grid" ? "active" : ""}
                    onClick={() => setView("grid")}
                  >
                    <LayoutGrid size={15} />
                  </button>
                  <button
                    aria-label="列表视图"
                    aria-pressed={view === "list"}
                    className={view === "list" ? "active" : ""}
                    onClick={() => setView("list")}
                  >
                    <List size={17} />
                  </button>
                </div>
              </div>
            </div>
            <div className="filter-chips">
              <button
                className={group === "all" ? "active" : ""}
                onClick={() => setGroup("all")}
              >
                全部服务器 <span>{servers.length}</span>
              </button>
              {groups.map((g) => (
                <button
                  key={g}
                  className={group === g ? "active" : ""}
                  onClick={() => setGroup(g)}
                >
                  {g}
                </button>
              ))}
            </div>
            {visible.length ? (
              <div
                className={`server-grid ${view === "list" ? "list-view" : ""}`}
              >
                {visible.map((server) => (
                  <ServerCard
                    key={server.id}
                    server={server}
                    interval={snapshot.interval}
                    clock={clock}
                  />
                ))}
              </div>
            ) : (
              <div className="empty-state">
                <Box size={30} />
                <h3>没有匹配的服务器</h3>
                <p>尝试更换关键词、分组或连接状态。</p>
                <button
                  onClick={() => {
                    setSearch("");
                    setGroup("all");
                    setStatus("all");
                  }}
                >
                  清除筛选
                </button>
              </div>
            )}
          </section>
          <footer className="main-footer">
            <span>
              <ShieldCheck size={13} />
              通过 SSH 连接，为简单而生。
            </span>
            <span>
              <Network size={13} />
              AIO Server Status<span className="footer-separator">/</span>v0.2.0
            </span>
          </footer>
        </main>
      </div>
    </div>
  );
}
