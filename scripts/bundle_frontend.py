"""Copy the validated production dashboard into the Python package."""

import shutil
from pathlib import Path

root = Path(__file__).resolve().parents[1]
source = root / "fe" / "dist"
target = root / "aio_server_status" / "static"
if not (source / "index.html").is_file() or not list((source / "assets").glob("*.js")):
    raise SystemExit("Missing frontend build. Run npm ci and npm run build in fe/ first.")
if target.exists():
    shutil.rmtree(target)
shutil.copytree(source, target)
print(f"Bundled dashboard: {target}")
