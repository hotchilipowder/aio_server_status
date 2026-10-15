# 常见问题

## `Host key verification failed`

以运行服务的同一用户执行 `ssh alias`，核对主机指纹后写入 `known_hosts`。如果指纹变化，先确认服务器变更的原因。工具不会自动关闭校验。

## `Permission denied (publickey)`

运行 `ssh -o BatchMode=yes alias 'uname -s'` 检查免交互认证。确认密钥、用户名和 ssh-agent 已正确配置。加密私钥先用 `ssh-add` 解锁；systemd 服务需单独配置可用的密钥或 agent 环境。

## 主机离线 / 连接超时

检查别名、网络、端口及 `ProxyJump`。采集会等待约 1 秒，慢网络可提高 `timeout`。每台服务器单独失败不会阻塞其他采集，单轮总时长还受服务器数量与 `concurrency` 限制。

## 没有 GPU 信息

只支持 NVIDIA 且需要远端已安装驱动与 `nvidia-smi`。未安装时不影响其他指标，工具不会自动安装驱动。

## 页面提示需要构建前端

源码安装没有携带前端产物。按顺序执行 `cd fe && npm ci && npm run build`，回到根目录后执行 `uv run --no-sync python scripts/bundle_frontend.py`。GitHub Release 的 wheel 已包含前端，推荐直接下载安装。API 可以在未构建前端时独立使用。

## 页面数据不再更新

检查控制机上的服务进程、浏览器网络与访问令牌。页面会保留上次快照，同时显示连接或数据过期提示，不会静默切换到模拟数据。演示必须显式使用 `?demo=1` 或 Pages 的演示构建。

## 为什么不支持 Windows / macOS 目标

探针读取 Linux `/proc`。控制机可以是 macOS，但目标必须是 Linux。其他系统会返回明确的采集错误。
