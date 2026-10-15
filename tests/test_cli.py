import pytest

from aio_server_status.cli import main
from aio_server_status.config import load_config


def test_init_creates_working_template_and_wont_overwrite(tmp_path):
    path = tmp_path / "servers.yaml"
    assert main(["init", "--config", str(path)]) == 0
    assert load_config(path).servers[0].host == "my-server"
    original = path.read_text()
    with pytest.raises(SystemExit) as exc:
        main(["init", "--config", str(path)])
    assert exc.value.code == 2
    assert path.read_text() == original


def test_bad_config_exits_cleanly(tmp_path, capsys):
    with pytest.raises(SystemExit) as exc:
        main(["serve", "--config", str(tmp_path / "missing")])
    assert exc.value.code == 2
    assert "init" in capsys.readouterr().err
