# 部署与 GitHub Pages

## 从 GitHub Release 部署

从 [最新 Release](https://github.com/hotchilipowder/aio_server_status/releases/latest) 下载 wheel，然后安装：

```bash
uv tool install ./aio_server_status-0.2.0-py3-none-any.whl
aio-server-status init
# 编辑 servers.yaml，填入 SSH 别名。
aio-server-status check
aio-server-status serve
```

wheel 和 Python 源码包都内含已构建前端，不需要安装 Node。每个 Release 同时提供独立前端压缩包和校验和。Linux 校验下载文件可使用 `sha256sum --check SHA256SUMS`；macOS 使用 `shasum -a 256 --check SHA256SUMS`（需要把清单中的三个文件都下载到同一目录）。

升级时对新版本 wheel 文件或 URL 使用 `uv tool install --force <wheel>`，再重启监控服务。

## SSH 隧道

建议在能连接全部目标的控制机上运行，远程查看时使用：

```bash
ssh -L 8080:127.0.0.1:8080 your-control-machine
```

打开 <http://127.0.0.1:8080>，网页和采集流量均可通过 SSH 完成。

## Linux systemd

对运行服务的用户执行 `uv tool install` 后，用 `command -v aio-server-status` 确认路径，再保存 `/etc/systemd/system/aio-server-status.service`。示例用户为 `monitor`，配置为 `/opt/aio_server_status/servers.yaml`：

```ini
[Unit]
Description=AIO SSH Server Status
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=monitor
WorkingDirectory=/opt/aio_server_status
ExecStart=/home/monitor/.local/bin/aio-server-status serve --config /opt/aio_server_status/servers.yaml
Restart=on-failure
RestartSec=5
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now aio-server-status
journalctl -u aio-server-status -f
```

服务用户须拥有 SSH 配置、可信 `known_hosts` 和可用密钥。终端的 ssh-agent 环境不会自动进入 systemd；按需提供可用的 `SSH_AUTH_SOCK`。不要提交真实配置或私钥。

## 独立前端包

Release 的 `aio-server-status-frontend-<version>.tar.gz` 解压后直接包含 `index.html` 和 `assets/`。适合由已有 Web 服务器提供页面，再把同源的 `/api/` 反向代理到控制机的 HTTP 服务；静态前端本身不能执行 SSH。普通部署使用 wheel 内置前端即可。

## 发布 GitHub Release

1. 同步 `pyproject.toml`、`aio_server_status/__init__.py` 和 `fe/package.json` 中的版本；涉及依赖或项目版本时更新并提交 `uv.lock`。
2. 提交代码并创建对应标签，例如 `git tag v0.2.0`，然后 `git push origin v0.2.0`。
3. `.github/workflows/release.yml` 调用完整 CI，测试通过后上传 wheel、源码包、独立前端和 `SHA256SUMS`。

版本标签必须等于 `v` 加项目版本；不匹配会在发布前失败。Release job 只下载已测试的产物，并校验版本、文件列表和 SHA-256，只有该 job 获得 `contents: write`。重跑同一标签会更新对应 Release 文件，不需要 PyPI 账号或额外发布密钥。

## Sphinx 与 GitHub Pages

`.github/workflows/pages.yml` 使用以下命令构建 Sphinx 文档：

```bash
uv sync --frozen --only-group docs
uv run --no-sync sphinx-build -b html -W --keep-going docs docs/_build/html
```

仪表盘以演示模式打包到输出目录的 `/demo/`。在仓库 **Settings → Pages → Build and deployment → Source** 中选择 **GitHub Actions**，默认分支推送后发布，也可手动触发。

网站首页是 Sphinx 文档，演示使用明确标注的模拟数据。Pages 不运行 Python 或 SSH，不需要服务器密钥。PR 只构建文档，不获得 Pages 部署权限。
