# 开发与贡献

## 目录结构

```text
aio_server_status/   SSH 采集、监控、HTTP 服务和命令行
fe/src/              React + TypeScript 仪表盘
tests/               后端及 Release 产物验证测试
docs/conf.py         Sphinx 配置
docs/*.md            MyST 文档源文件
scripts/             前端打包、Release 产物和集成验证
.github/workflows/   uv CI、GitHub Release、Sphinx Pages
pyproject.toml       项目依赖、工具依赖组和打包元数据
uv.lock              提交到仓库的 Python 依赖锁文件
```

## 初始化

需要 uv 0.13.1+（CI 固定 0.13.1）、Python 3.11+、OpenSSH；构建前端需要 Node.js 22.12+，推荐 24 LTS。

```bash
uv sync --frozen --all-groups
npm --prefix fe ci
npm --prefix fe run build
uv run --no-sync python scripts/bundle_frontend.py
```

运行时依赖放在 `[project.dependencies]`，工具放在 `[dependency-groups]`：默认 `dev` 用于测试和代码检查，`docs` 用于 Sphinx，`build` 用于发布包校验。`uv sync` 负责创建并同步 `.venv`，无需手动创建或激活。

添加运行时依赖使用 `uv add package`；开发依赖使用 `uv add --dev package`；文档依赖使用 `uv add --group docs package`。更新后提交 `pyproject.toml` 和 `uv.lock`。CI 使用 `--frozen` 并检查锁文件一致性。

## 测试与检查

```bash
uv lock --check
uv run --no-sync ruff check .
uv run --no-sync ruff format --check .
uv run --no-sync python -m pytest
npm --prefix fe run format:check
npm --prefix fe test
npm --prefix fe run build
uv run --no-sync sphinx-build -b html -W --keep-going docs docs/_build/html
```

Ubuntu CI 启动临时 sshd，以临时密钥执行真实 Linux 采集；不需要真实服务器。macOS 本机默认跳过该项测试。

## 本地开发

```bash
uv run --frozen aio-server-status init
# 修改 servers.yaml 后：
uv run --frozen aio-server-status serve
```

前端开发另开终端执行 `npm --prefix fe run dev`，API 代理到本机 8080；`?demo=1` 使用模拟数据。前端相对资源路径支持 Python 打包和 Pages 子目录，真实服务断开不会自动切换为演示。

## 构建 Release 文件

```bash
npm --prefix fe run build
uv run --no-sync python scripts/bundle_frontend.py
uv build
uv run --no-sync twine check dist/*.whl dist/*.tar.gz
uv run --no-sync python scripts/prepare_release.py --tag v0.2.0
```

`dist/release/` 包含 wheel、源码包、独立前端压缩包和 `SHA256SUMS`。脚本确认 wheel 中的前端与当前构建逐字节一致，并拒绝错误版本标签。先构建前端再打 Python 包；GitHub Release 工作流会完成全部步骤。

## Sphinx 文档

文档使用 MyST 保留 Markdown 写法，Furo 提供主题。导航位于 `docs/index.md` 的 `toctree`，新页面须加入导航。输出为 `docs/_build/html/`，通过 `sphinx.ext.githubpages` 生成 `.nojekyll`。

```bash
uv run --group docs sphinx-build -b html -W --keep-going docs docs/_build/html
uv run --no-project python -m http.server 8000 --directory docs/_build/html
```

打开 <http://127.0.0.1:8000>。源文档中的 `.md` 链接由 Sphinx 转成 `.html`；前端指向已发布文档时也使用 `.html` 路径。
