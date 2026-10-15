"""Prepare only tested distributions, a static dashboard and their checksums."""

import argparse
import hashlib
import shutil
import tarfile
import tomllib
import zipfile
from pathlib import Path


def _metadata(root: Path, tag: str | None):
    metadata = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))["project"]
    version = metadata["version"]
    if tag is not None and tag != f"v{version}":
        raise ValueError(f"Release tag {tag!r} must match pyproject.toml version v{version}")
    name = metadata["name"].replace("-", "_")
    return name, version


def verify_release(root: Path, tag: str | None = None) -> None:
    name, version = _metadata(root, tag)
    output = root / "dist" / "release"
    expected = {
        f"{name}-{version}-py3-none-any.whl",
        f"{name}-{version}.tar.gz",
        f"aio-server-status-frontend-{version}.tar.gz",
    }
    if not output.is_dir() or {path.name for path in output.iterdir()} != expected | {"SHA256SUMS"}:
        raise ValueError(
            "Release assets must contain exactly the current wheel, source, frontend and checksums"
        )
    checksums = {}
    for line in (output / "SHA256SUMS").read_text(encoding="utf-8").splitlines():
        checksum, filename = line.split("  ")
        if filename in checksums:
            raise ValueError("Duplicate entry in release checksums")
        checksums[filename] = checksum
    if checksums.keys() != expected:
        raise ValueError("Release checksum manifest does not match the expected assets")
    for filename, checksum in checksums.items():
        if hashlib.sha256((output / filename).read_bytes()).hexdigest() != checksum:
            raise ValueError(f"Release checksum mismatch: {filename}")


def prepare_release(root: Path, tag: str | None = None) -> Path:
    name, version = _metadata(root, tag)
    dist = root / "dist"
    wheel = dist / f"{name}-{version}-py3-none-any.whl"
    source = dist / f"{name}-{version}.tar.gz"
    if not wheel.is_file():
        raise ValueError("Missing wheel; build and validate the bundled package with uv build first")
    if not source.is_file():
        raise ValueError("Missing source distribution; run uv build first")
    frontend = root / "fe" / "dist"
    assets = sorted((frontend / "assets").rglob("*"))
    paths = [frontend / "index.html", *(path for path in assets if path.is_file())]
    if any(path.is_symlink() for path in [frontend, frontend / "assets", *assets, *paths]):
        raise ValueError("The frontend must not contain symlinks")
    if not paths[0].is_file() or not any(path.suffix == ".js" for path in paths):
        raise ValueError("Missing frontend build; run npm ci and npm run build in fe/ first")
    with zipfile.ZipFile(wheel) as archive:
        for path in paths:
            member = f"{name}/static/{path.relative_to(frontend).as_posix()}"
            if member not in archive.namelist() or archive.read(member) != path.read_bytes():
                raise ValueError("Wheel frontend does not match fe/dist; bundle the frontend and rebuild")
        if f"{name}/probe.sh" not in archive.namelist():
            raise ValueError("Wheel is missing the SSH probe")
    output = dist / "release"
    if output.exists():
        shutil.rmtree(output)
    output.mkdir(parents=True)
    for path in (wheel, source):
        shutil.copy2(path, output / path.name)
    with tarfile.open(output / f"aio-server-status-frontend-{version}.tar.gz", "w:gz") as archive:
        for path in paths:
            archive.add(path, arcname=path.relative_to(frontend).as_posix())
    checksums = [
        f"{hashlib.sha256(path.read_bytes()).hexdigest()}  {path.name}\n" for path in sorted(output.iterdir())
    ]
    (output / "SHA256SUMS").write_text("".join(checksums), encoding="utf-8")
    verify_release(root, tag)
    return output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tag", help="Expected version tag, e.g. v0.2.0")
    parser.add_argument(
        "--verify-only", action="store_true", help="Verify downloaded assets without rebuilding"
    )
    args = parser.parse_args()
    try:
        root = Path(__file__).resolve().parents[1]
        if args.verify_only:
            verify_release(root, tag=args.tag)
            print("Release version, assets and checksums are valid.")
            return
        output = prepare_release(root, tag=args.tag)
    except (ValueError, OSError, zipfile.BadZipFile) as exc:
        parser.error(str(exc))
    print(f"Release assets and SHA256SUMS: {output}")


if __name__ == "__main__":
    main()
