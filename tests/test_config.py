import pytest

from aio_server_status.config import ConfigError, load_config


def write_config(tmp_path, text):
    path = tmp_path / "servers.yaml"
    path.write_text(text)
    return path


def test_minimal_ssh_aliases(tmp_path):
    config = load_config(write_config(tmp_path, "servers:\n  - production\n  - gpu-box\n"))
    assert [host.host for host in config.servers] == ["production", "gpu-box"]
    assert config.interval == 10
    assert config.listen == "127.0.0.1"


def test_explicit_host_and_relative_identity(tmp_path):
    config = load_config(
        write_config(
            tmp_path,
            """
interval: 5
servers:
  - host: example.org
    name: Production
    user: monitor
    port: 2222
    identity_file: keys/id_ed25519
    group: EU
""",
        )
    )
    host = config.servers[0]
    assert host.identity_file == str(tmp_path / "keys/id_ed25519")
    assert (host.name, host.port, host.group) == ("Production", 2222, "EU")


@pytest.mark.parametrize(
    "text",
    [
        "servers: []",
        "servers: [-oProxyCommand=bad]",
        "servers: [same, same]",
        "interval: 0\nservers: [ok]",
        "servers: [{host: ok, port: true}]",
        "servers: [{host: ok, port: 70000}]",
        "servers: [{host: ok, typo: 1}]",
        "server: [ok]",
        "servers: [{host: 'bad host'}]",
        "servers: [123]",
        "timeout: .nan\nservers: [ok]",
        "concurrency: false\nservers: [ok]",
        "interval: 5\ninterval: 10\nservers: [ok]",
    ],
)
def test_invalid_config_is_actionable(tmp_path, text):
    with pytest.raises(ConfigError):
        load_config(write_config(tmp_path, text))


def test_missing_config_has_helpful_error(tmp_path):
    with pytest.raises(ConfigError, match="init"):
        load_config(tmp_path / "missing.yaml")
