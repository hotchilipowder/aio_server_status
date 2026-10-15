# 配置参考

最小配置直接使用 `~/.ssh/config` 中的别名：

```yaml
servers:
  - web-prod
  - gpu-server
```

完整示例：

```yaml
title: My infrastructure
interval: 10
timeout: 10
concurrency: 10
listen: 127.0.0.1
port: 8080
servers:
  - host: web-prod
    name: Web production
    group: Production
  - host: 192.0.2.20
    name: GPU worker
    user: monitor
    port: 2222
    identity_file: ~/.ssh/id_ed25519
    group: Compute
```

| 字段 | 默认值 | 说明 |
| --- | --- | --- |
| `servers` | 必填 | 至少一台服务器；字符串别名或配置对象 |
| `title` | AIO Server Status | 页面标题 |
| `interval` | 10 | 轮询开始时间之间的目标间隔，至少 2 秒；若本轮更慢则结束后继续 |
| `timeout` | 10 | 单台服务器完整 SSH 采集超时，至少 2 秒 |
| `concurrency` | 10 | 最大并发 SSH 数，1–100 |
| `listen` | 127.0.0.1 | HTTP 监听地址 |
| `port` | 8080 | HTTP 端口，1–65535 |
| `servers[].host` | 必填 | SSH 别名、域名或 IP；列表中必须唯一 |
| `servers[].name` | host | 页面显示名称 |
| `servers[].group` | Default | 用于前端分组 |
| `servers[].user` | SSH 配置 | 显式指定远程用户名 |
| `servers[].port` | SSH 配置 | 只在指定时覆盖 SSH 配置端口 |
| `servers[].identity_file` | SSH 配置 | 密钥路径；`~` 展开，相对路径以 YAML 文件所在目录为基准 |

未知字段、重复 YAML 键、重复主机、非法类型和越界数值会在启动时报告错误。密码和任意远程命令不是配置项。

## SSH 配置优先级

没有在 YAML 指定的连接项直接由 OpenSSH 处理，因此密钥代理、跳板机和现有 SSH 配置均可复用。命令使用 `BatchMode=yes` 和 `StrictHostKeyChecking=yes`。需要密码或询问式 MFA 的连接请先配置适合自动采集的密钥认证。

## API 访问令牌

通过环境变量启用，令牌不会写入配置、前端构建或状态响应：

```bash
export AIO_STATUS_TOKEN='replace-with-your-own-random-token'
aio-server-status serve
```

打开页面后输入令牌。令牌仅保存在当前标签页内存，刷新页面需要重新输入。默认监听本机；远程访问优先使用 SSH 隧道。若主动设置 `listen: 0.0.0.0`，同时设置令牌并通过 HTTPS 反向代理访问。
