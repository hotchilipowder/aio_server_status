import { useEffect, useState } from "react";
import { Activity, KeyRound, RefreshCw } from "lucide-react";
import { Dashboard } from "./Dashboard";
import { demoSnapshot } from "./demo";
import type { Snapshot } from "./model";

export default function App() {
  const demo =
    new URLSearchParams(window.location.search).get("demo") === "1" ||
    import.meta.env.VITE_DEMO === "true";
  const [snapshot, setSnapshot] = useState<Snapshot | null>(() =>
    demo ? demoSnapshot() : null,
  );
  const [error, setError] = useState<string | null>(null);
  const [token, setToken] = useState("");
  const [draftToken, setDraftToken] = useState("");
  const [needsAuth, setNeedsAuth] = useState(false);
  const [refresh, setRefresh] = useState(0);
  const [refreshing, setRefreshing] = useState(false);
  useEffect(() => {
    if (demo) {
      const timer = setInterval(() => setSnapshot(demoSnapshot()), 10000);
      return () => clearInterval(timer);
    }
    let disposed = false;
    let timer: ReturnType<typeof setTimeout>;
    let controller: AbortController;
    async function poll() {
      controller = new AbortController();
      const timeout = setTimeout(() => controller.abort(), 8000);
      setRefreshing(true);
      let interval = 5;
      try {
        const response = await fetch("./api/status", {
          cache: "no-store",
          signal: controller.signal,
          headers: token ? { Authorization: `Bearer ${token}` } : {},
        });
        if (disposed) return;
        if (response.status === 401) {
          setNeedsAuth(true);
          setError("请输入正确的访问令牌以连接监控服务。");
          return;
        }
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        const data: Snapshot = await response.json();
        if (
          !Array.isArray(data.servers) ||
          !Number.isFinite(data.interval) ||
          data.interval <= 0 ||
          typeof data.generated_at !== "string"
        )
          throw new Error("状态数据格式不正确");
        if (disposed) return;
        setSnapshot(data);
        setError(null);
        setNeedsAuth(false);
        interval = Math.max(2, Math.min(10, data.interval));
      } catch (reason) {
        if (!disposed)
          setError(
            `无法连接监控服务：${reason instanceof Error ? reason.message : "网络错误"}。请检查服务是否运行。`,
          );
      } finally {
        clearTimeout(timeout);
        if (!disposed) {
          setRefreshing(false);
          timer = setTimeout(poll, interval * 1000);
        }
      }
    }
    void poll();
    return () => {
      disposed = true;
      clearTimeout(timer);
      controller?.abort();
    };
  }, [demo, token, refresh]);
  if (!snapshot || needsAuth)
    return (
      <div className="connection-screen">
        <div className="connection-panel">
          <div className="brand-mark">
            <Activity size={30} />
          </div>
          <div className="eyebrow">AIO SERVER STATUS</div>
          <h1>
            {needsAuth
              ? "连接你的工作空间"
              : error
                ? "暂时无法连接"
                : "正在连接监控服务"}
          </h1>
          <p role={error ? "alert" : undefined}>
            {error ?? "正在获取服务器的最新状态，请稍候。"}
          </p>
          {needsAuth ? (
            <form
              onSubmit={(e) => {
                e.preventDefault();
                setToken(draftToken);
                setRefresh((v) => v + 1);
              }}
            >
              <label htmlFor="access-token">访问令牌</label>
              <div className="token-input">
                <KeyRound size={17} />
                <input
                  id="access-token"
                  type="password"
                  value={draftToken}
                  onChange={(e) => setDraftToken(e.target.value)}
                  autoComplete="off"
                  required
                />
              </div>
              <button type="submit">连接监控服务</button>
              <small>令牌仅保留在当前标签页内存中。</small>
            </form>
          ) : (
            <button
              onClick={() => setRefresh((v) => v + 1)}
              disabled={refreshing}
            >
              <RefreshCw size={14} />
              重新连接
            </button>
          )}
          <a href="?demo=1">查看演示工作空间 ↗</a>
        </div>
      </div>
    );
  return (
    <Dashboard
      snapshot={snapshot}
      demo={demo}
      error={error}
      refreshing={refreshing}
      onRefresh={() => {
        if (demo) setSnapshot(demoSnapshot());
        else setRefresh((v) => v + 1);
      }}
    />
  );
}
