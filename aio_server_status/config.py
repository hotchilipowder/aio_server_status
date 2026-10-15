"""Small, strict configuration model; connection defaults belong to OpenSSH."""

import math
import re
from dataclasses import dataclass
from pathlib import Path

import yaml


class ConfigError(ValueError):
    """A user-facing configuration error."""


class UniqueLoader(yaml.SafeLoader):
    pass


def _unique_mapping(loader, node):
    result = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node)
        if not isinstance(key, str) or key in result:
            raise ConfigError(f"Invalid or duplicate YAML key: {key!r}")
        result[key] = loader.construct_object(value_node)
    return result


UniqueLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _unique_mapping)


@dataclass(frozen=True)
class Host:
    host: str
    name: str
    group: str = "Default"
    user: str | None = None
    port: int | None = None
    identity_file: str | None = None


@dataclass(frozen=True)
class Config:
    servers: tuple[Host, ...]
    interval: float = 10
    timeout: float = 10
    concurrency: int = 10
    listen: str = "127.0.0.1"
    port: int = 8080
    title: str = "AIO Server Status"


def _number(value, name, minimum, maximum, integer=False):
    expected = (int,) if integer else (int, float)
    if (
        isinstance(value, bool)
        or not isinstance(value, expected)
        or not math.isfinite(value)
        or not minimum <= value <= maximum
    ):
        raise ConfigError(f"{name} must be {'an integer' if integer else 'a number'} in {minimum}..{maximum}")
    return value


def _text(value, name):
    if not isinstance(value, str) or not value.strip():
        raise ConfigError(f"{name} must be a non-empty string")
    return value


def load_config(path: Path | str) -> Config:
    path = Path(path).expanduser().resolve()
    try:
        data = yaml.load(path.read_text(encoding="utf-8"), Loader=UniqueLoader)
    except OSError as exc:
        raise ConfigError(f"Cannot read {path}. Run 'aio-server-status init' first. {exc.strerror}") from exc
    except yaml.YAMLError as exc:
        raise ConfigError(f"Invalid YAML: {exc}") from exc
    allowed = {"servers", "interval", "timeout", "concurrency", "listen", "port", "title"}
    if not isinstance(data, dict) or set(data) - allowed:
        raise ConfigError(f"Expected configuration keys: {', '.join(sorted(allowed))}")
    servers = data.get("servers")
    if not isinstance(servers, list) or not servers:
        raise ConfigError("servers must be a non-empty list of SSH aliases or host objects")
    hosts, seen = [], set()
    host_fields = {"host", "name", "group", "user", "port", "identity_file"}
    for index, item in enumerate(servers):
        if isinstance(item, str):
            item = {"host": item}
        if not isinstance(item, dict) or set(item) - host_fields:
            raise ConfigError(f"servers[{index}] must be a host object with keys {sorted(host_fields)}")
        host = _text(item.get("host"), f"servers[{index}].host")
        if not re.fullmatch(r"[a-zA-Z0-9_][a-zA-Z0-9_.@:%+\-\[\]]*", host):
            raise ConfigError(f"Invalid SSH alias or address: {host!r}")
        if host in seen:
            raise ConfigError(f"Duplicate host: {host}")
        seen.add(host)
        port = _number(item["port"], "host.port", 1, 65535, True) if "port" in item else None
        user = item.get("user")
        if user is not None and not re.fullmatch(r"[a-zA-Z0-9_][a-zA-Z0-9_.\-]*", _text(user, "user")):
            raise ConfigError("Invalid SSH username")
        identity = item.get("identity_file")
        if identity is not None:
            identity = Path(_text(identity, "identity_file")).expanduser()
            identity = str(identity if identity.is_absolute() else path.parent / identity)
        hosts.append(
            Host(
                host=host,
                name=_text(item.get("name", host), "name"),
                group=_text(item.get("group", "Default"), "group"),
                user=user,
                port=port,
                identity_file=identity,
            )
        )
    return Config(
        servers=tuple(hosts),
        interval=_number(data.get("interval", 10), "interval", 2, 3600),
        timeout=_number(data.get("timeout", 10), "timeout", 2, 300),
        concurrency=_number(data.get("concurrency", 10), "concurrency", 1, 100, True),
        listen=_text(data.get("listen", "127.0.0.1"), "listen"),
        port=_number(data.get("port", 8080), "port", 1, 65535, True),
        title=_text(data.get("title", "AIO Server Status"), "title"),
    )
