# 快速开始

## 1. 准备 SSH

在控制机上确认可以免交互连接目标 Linux 服务器：

```bash
ssh my-server
ssh -o BatchMode=yes my-server 'uname -s'
```

首次连接时核对并接受正确的主机指纹。工具严格校验 `known_hosts`，不自动信任陌生主机。使用密钥或已解锁的 ssh-agent，不在 YAML 保存密码。

例如现有的 `~/.ssh/config`：

```text
Host my-server
    HostName 192.0.2.10
    User monitor
    IdentityFile ~/.ssh/id_ed25519

Host internal-gpu
    HostName 10.0.0.10
    User monitor
    ProxyJump my-server
```

## 2. 下载预构建安装包

安装 [uv](https://docs.astral.sh/uv/getting-started/installation/)，从 [GitHub Releases](https://github.com/hotchilipowder/aio_server_status/releases/latest) 下载当前版本的 `.whl` 文件：

```bash
# 示例版本为 0.2.0，请使用实际下载的文件名。
uv tool install ./aio_server_status-0.2.0-py3-none-any.whl
```

安装包包含已构建前端，无需 Node 或单独部署前端。Python 需要 3.11+；uv 可以管理所需 Python。若命令不在 PATH，运行 `uv tool update-shell` 并重新打开终端。

也可在版本发布后直接安装 wheel URL：

```bash
uv tool install 'https://github.com/hotchilipowder/aio_server_status/releases/download/v0.2.0/aio_server_status-0.2.0-py3-none-any.whl'
```

## 3. 配置服务器

```bash
aio-server-status init
```

编辑 `servers.yaml`：

```yaml
servers:
  - my-server
  - internal-gpu
```

## 4. 检查并启动

```bash
aio-server-status check
aio-server-status serve
```

打开 <http://127.0.0.1:8080>。单次采集约 1 秒，失败达到超时后显示离线。`check` 在任意主机失败时返回非零退出码。指定配置文件：

```bash
aio-server-status serve --config /path/to/servers.yaml
```

修改 YAML 后重启进程。更多设置见[配置参考](configuration.md)，源码安装见[开发文档](development.md)。
