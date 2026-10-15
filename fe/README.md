# AIO dashboard

React + TypeScript + Vite 静态仪表盘，由 Python 服务提供。

```bash
npm ci
npm run dev      # API 代理到 127.0.0.1:8080
npm test
npm run build
```

要求 Node.js 22.12+，推荐 24 LTS。只看界面可访问 `http://localhost:5173/?demo=1`。正式部署在项目根目录执行 `uv run --no-sync python scripts/bundle_frontend.py`，然后启动 Python 服务；无需独立运行 Node。

GitHub Pages 通过 `VITE_DEMO=true npm run build` 生成演示版本。演示始终标注模拟数据；实时服务断开不会自动切换到演示。

GitHub Release 同时提供独立前端压缩包和包含前端的 Python wheel；普通部署直接下载 wheel，无需 Node。
