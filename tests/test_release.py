import hashlib
import io
import tarfile
import zipfile

import pytest

from scripts.prepare_release import prepare_release


@pytest.fixture
def release_tree(tmp_path):
    (tmp_path / "pyproject.toml").write_text('[project]\nname = "aio_server_status"\nversion = "0.2.0"\n')
    frontend = tmp_path / "fe" / "dist"
    (frontend / "assets").mkdir(parents=True)
    (frontend / "index.html").write_text('<div id="root"></div>')
    (frontend / "assets" / "dashboard.js").write_text('console.log("dashboard")')
    (frontend / "assets" / "dashboard.css").write_text("body { color: green; }")
    # Only intended public assets enter the standalone bundle.
    (frontend / "servers.yaml").write_text("servers: [private]")
    dist = tmp_path / "dist"
    dist.mkdir()
    with zipfile.ZipFile(dist / "aio_server_status-0.2.0-py3-none-any.whl", "w") as archive:
        archive.writestr("aio_server_status/probe.sh", "#!/bin/sh\n")
        for path in [frontend / "index.html", *(frontend / "assets").iterdir()]:
            archive.writestr(
                f"aio_server_status/static/{path.relative_to(frontend).as_posix()}", path.read_bytes()
            )
    with tarfile.open(dist / "aio_server_status-0.2.0.tar.gz", "w:gz") as archive:
        info = tarfile.TarInfo("aio_server_status-0.2.0/pyproject.toml")
        data = (tmp_path / "pyproject.toml").read_bytes()
        info.size = len(data)
        archive.addfile(info, io.BytesIO(data))
    return tmp_path


def test_release_contains_prebuilt_frontend_and_verified_checksums(release_tree):
    output = prepare_release(release_tree, tag="v0.2.0")
    expected = {
        "aio_server_status-0.2.0-py3-none-any.whl",
        "aio_server_status-0.2.0.tar.gz",
        "aio-server-status-frontend-0.2.0.tar.gz",
        "SHA256SUMS",
    }
    assert {path.name for path in output.iterdir()} == expected
    with tarfile.open(output / "aio-server-status-frontend-0.2.0.tar.gz") as archive:
        assert set(archive.getnames()) == {"index.html", "assets/dashboard.js", "assets/dashboard.css"}
    for line in (output / "SHA256SUMS").read_text().splitlines():
        checksum, name = line.split("  ")
        assert hashlib.sha256((output / name).read_bytes()).hexdigest() == checksum


def test_release_rejects_wrong_tag(release_tree):
    with pytest.raises(ValueError, match="tag"):
        prepare_release(release_tree, tag="v0.3.0")


def test_release_rejects_wheel_with_old_frontend(release_tree):
    (release_tree / "fe/dist/assets/dashboard.js").write_text("updated dashboard")
    with pytest.raises(ValueError, match="frontend"):
        prepare_release(release_tree)


def test_release_requires_dashboard_assets(release_tree):
    (release_tree / "fe/dist/index.html").unlink()
    with pytest.raises(ValueError, match="frontend"):
        prepare_release(release_tree)


def test_release_requires_built_distribution(release_tree):
    next((release_tree / "dist").glob("*.whl")).unlink()
    with pytest.raises(ValueError, match="wheel"):
        prepare_release(release_tree)


def test_release_rejects_symlinked_frontend_asset(release_tree):
    asset = release_tree / "fe/dist/assets/dashboard.js"
    asset.unlink()
    secret = release_tree / "secret"
    secret.write_text("private")
    asset.symlink_to(secret)
    with pytest.raises(ValueError, match="symlink"):
        prepare_release(release_tree)


def test_downloaded_release_is_verified_before_publication(release_tree):
    from scripts.prepare_release import verify_release

    output = prepare_release(release_tree)
    verify_release(release_tree, tag="v0.2.0")
    (output / "aio-server-status-frontend-0.2.0.tar.gz").write_bytes(b"corrupted")
    with pytest.raises(ValueError, match="checksum"):
        verify_release(release_tree, tag="v0.2.0")


def test_downloaded_release_rejects_mismatched_tag(release_tree):
    from scripts.prepare_release import verify_release

    prepare_release(release_tree)
    with pytest.raises(ValueError, match="tag"):
        verify_release(release_tree, tag="v0.9.0")


def test_downloaded_release_rejects_unexpected_asset(release_tree):
    from scripts.prepare_release import verify_release

    output = prepare_release(release_tree)
    (output / "old-package.whl").write_bytes(b"old build")
    with pytest.raises(ValueError, match="assets"):
        verify_release(release_tree)
