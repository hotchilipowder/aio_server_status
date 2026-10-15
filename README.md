# AIO Server Status

**只需 SSH，就能掌握每一台 Linux 服务器的状态。**

在一台控制机上运行，通过现有 SSH 连接采集 CPU、内存、磁盘、网络、负载和 NVIDIA GPU，在自动刷新的网页里查看。被监控服务器无需安装 agent、Python、数据库或开放额外端口。

[使用文档](https://hotchilipowder.github.io/aio_server_status/) · [下载 Release](https://github.com/hotchilipowder/aio_server_status/releases/latest) · [界面演示](https://hotchilipowder.github.io/aio_server_status/demo/) · [配置示例](servers.example.yaml)

![监控仪表盘（模拟数据）](docs/images/dashboard.png)

## 从 GitHub Release 安装

需要 [uv](https://docs.astral.sh/uv/getting-started/installation/)、Python 3.11+ 和 OpenSSH 客户端。控制机可以是 Linux 或 macOS；首次连接先运行 `ssh my-server` 验证主机指纹，并确保密钥或 ssh-agent 可以免交互认证。

到 [Releases](https://github.com/hotchilipowder/aio_server_status/releases/latest) 下载 `.whl` 文件，它已经包含前端。以 v0.2.0 为例：

```bash
uv tool install ./aio_server_status-0.2.0-py3-none-any.whl
aio-server-status init
```

也可以在该版本发布后直接从 GitHub Release URL 安装：

```bash
uv tool install 'https://github.com/hotchilipowder/aio_server_status/releases/download/v0.2.0/aio_server_status-0.2.0-py3-none-any.whl'
```

无需 Node、克隆仓库或自行构建前端。`uv tool` 会管理独立运行环境；若提示命令不在 PATH，执行 `uv tool update-shell` 后重新打开终端。

把生成的 `servers.yaml` 改为已有 SSH 别名：

```yaml
servers:
  - web-prod
  - gpu-server
```

```bash
aio-server-status check  # 检查连接和指标采集
aio-server-status serve  # 打开 http://127.0.0.1:8080
```

`~/.ssh/config` 的 `HostName`、`User`、`Port`、`IdentityFile`、`ProxyJump` 和 ssh-agent 直接生效。更多设置见[配置参考](docs/configuration.md)。

## Release 包含什么

| 文件 | 用途 |
| --- | --- |
| `aio_server_status-<version>-py3-none-any.whl` | 推荐安装包，内含后端、SSH 探针和已构建前端 |
| `aio_server_status-<version>.tar.gz` | 同样携带前端的 Python 源码包 |
| `aio-server-status-frontend-<version>.tar.gz` | 独立静态前端，可用于同源反向代理部署 |
| `SHA256SUMS` | 三个发布文件的 SHA-256 校验和 |

升级时使用新版本 wheel URL 执行 `uv tool install --force <wheel-url>`，然后重启服务。Release 由版本标签自动触发，详见[发布流程](docs/deployment.md)。

## 功能

- 多服务器并发采集、超时和失败隔离，保留最近 60 次采样。
- CPU、内存、Swap、磁盘、负载、运行时长、网卡速率及可选 NVIDIA GPU。
- 暗色响应式前端，支持搜索、分组、状态筛选、趋势和连接错误。
- 一份 YAML，使用 `init`、`check`、`serve` 完成配置。
- 默认仅监听本机，严格校验 SSH 主机指纹，支持 API Bearer Token。
- uv 管理依赖与锁文件；GitHub Actions 测试和打包；GitHub Release 提供安装包；Sphinx 文档发布到 GitHub Pages。

远程查看建议使用 SSH 隧道：

```bash
ssh -L 8080:127.0.0.1:8080 your-control-machine
```

Pages 承载 Sphinx 文档和模拟数据演示；实时 SSH 采集运行在你的控制机上。

## 源码开发与构建

仓库使用 uv 0.13.1+（CI 固定为 0.13.1），提交 `uv.lock`，不维护 requirements 文件。前端构建需要 Node.js 22.12+，推荐 24 LTS。

```bash
uv sync --frozen --all-groups
npm --prefix fe ci
npm --prefix fe run build
uv run --no-sync python scripts/bundle_frontend.py
uv run --no-sync python -m pytest
uv run --no-sync ruff check .
uv build
uv run --no-sync python scripts/prepare_release.py
```

源码启动：`uv run --frozen aio-server-status serve`。构建后的发布文件位于 `dist/release/`。

文档使用 Sphinx、MyST 和 Furo：

```bash
uv run --group docs sphinx-build -b html -W --keep-going docs docs/_build/html
```

本地预览：`uv run --no-project python -m http.server 8000 --directory docs/_build/html`。前端开发使用 `npm --prefix fe run dev`，API 会代理到 `127.0.0.1:8080`，`?demo=1` 可查看模拟数据。

## 参考与许可

参考目标为 [tornado_server_status](https://github.com/hotchilipowder/tornado_server_status)。重构时该链接公开访问返回 404，当前实现以简单配置和 SSH 采集要求为准，不宣称配置或 API 兼容。

[MIT License](LICENSE)
