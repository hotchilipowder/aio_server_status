# HTTP API

API 和静态页面使用同一个端口。默认仅本机访问，不启用跨域。

## `GET /healthz`

返回 `{"status": "ok"}`，用于判断 HTTP 服务存活，不代表所有服务器在线。不要求访问令牌。

## `GET /api/status`

返回缓存的最近一次状态；浏览器请求不会额外触发 SSH 采集。响应设为 `Cache-Control: no-store`。

```json
{
  "title": "AIO Server Status",
  "generated_at": "2026-10-15T12:00:00+00:00",
  "interval": 10,
  "servers": [
    {
      "id": "web-prod",
      "name": "web-prod",
      "group": "Default",
      "status": "online",
      "checked_at": "2026-10-15T12:00:00+00:00",
      "last_success_at": "2026-10-15T12:00:00+00:00",
      "latency_ms": 1200,
      "error": null,
      "metrics": {},
      "history": []
    }
  ]
}
```

`status` 为 `connecting`、`online` 或 `offline`。`latency_ms` 是完整 SSH 采集耗时（包括约 1 秒采样等待），并非 ping 延迟。上例省略指标内容；`metrics` 包含 `hostname`、`cpu_count`、`cpu_percent`、`memory`、`swap`、`load`、`uptime_seconds`、`network`、`disks` 和 `gpus`，单位见[指标文档](metrics.md)。

`history` 最多保留 60 个 `{at, cpu_percent, memory_percent}` 采样点。失败时 `metrics` 为 `null`，历史当前点为空值。

启用令牌时：

```bash
curl -H "Authorization: Bearer $AIO_STATUS_TOKEN" http://127.0.0.1:8080/api/status
```

未提供正确令牌返回 HTTP 401。密钥路径、SSH 用户和配置对象不出现在状态响应中。`id` 仍是配置中的 SSH 别名或地址，页面数据本身可能包含主机名和连接错误，因此不应公开暴露。
