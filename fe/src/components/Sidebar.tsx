import {
  Activity,
  ArrowUpRight,
  BookOpen,
  ChevronDown,
  CircleHelp,
  LayoutGrid,
  ShieldCheck,
} from "lucide-react";
import type { Snapshot } from "../model";
import { DOCS_URL as docs } from "../links";

export function Sidebar({
  snapshot,
  group,
  onGroupChange,
  onReset,
}: {
  snapshot: Snapshot;
  group: string;
  onGroupChange: (value: string) => void;
  onReset: () => void;
}) {
  const servers = snapshot.servers;
  const groups = [...new Set(servers.map((server) => server.group))];
  return (
    <aside className="sidebar">
      <a href="./" className="brand">
        <span className="brand-mark">
          <Activity size={23} />
        </span>
        <span>
          AIO<span className="brand-small">SERVER STATUS</span>
        </span>
      </a>
      <div className="workspace">
        <span className="workspace-icon">M</span>
        <div>
          {snapshot.title}
          <small>SSH MONITORING</small>
        </div>
        <ChevronDown size={14} />
      </div>
      <div className="nav-label">工作空间</div>
      <button className="nav-item selected" onClick={onReset}>
        <LayoutGrid size={17} />
        总览<span className="nav-count">{servers.length}</span>
      </button>
      <div className="nav-label groups-label">
        服务器分组 <span>{groups.length}</span>
      </div>
      {groups.map((g) => (
        <button
          className={`nav-item ${group === g ? "group-selected" : ""}`}
          key={g}
          onClick={() => onGroupChange(group === g ? "all" : g)}
        >
          <span className="group-dot" />
          {g}
          <span className="group-count">
            {servers.filter((s) => s.group === g).length}
          </span>
        </button>
      ))}
      <div className="sidebar-bottom">
        <div className="ssh-note">
          <ShieldCheck size={19} />
          <strong>由 SSH 安全连接</strong>
          <p>无需 Agent，连接即监控。</p>
          <span>你的密钥始终留在控制机。</span>
        </div>
        <a className="nav-item" href={docs} target="_blank" rel="noreferrer">
          <BookOpen size={17} />
          使用文档
          <ArrowUpRight size={14} />
        </a>
        <a
          className="nav-item"
          href={`${docs}troubleshooting.html`}
          target="_blank"
          rel="noreferrer"
        >
          <CircleHelp size={17} />
          帮助与反馈
          <ArrowUpRight size={14} />
        </a>
        <div className="sidebar-footer">
          <span className="tiny-dot" />
          AIO v0.2.0<span>开源 · MIT</span>
        </div>
      </div>
    </aside>
  );
}
