#!/usr/bin/env bash
# Disposable Linux CI fixture. Never run against production SSH configuration.
set -euo pipefail
if [[ "${GITHUB_ACTIONS:-}" != "true" || "$(uname -s)" != Linux ]]; then
  echo 'This fixture is restricted to disposable GitHub Actions Linux runners.' >&2
  exit 1
fi
fixture_dir=$(mktemp -d)
cleanup() {
  result=$?
  if [[ "$result" != 0 && -f "$fixture_dir/sshd.log" ]]; then cat "$fixture_dir/sshd.log" >&2; fi
  if [[ -f "$fixture_dir/sshd.pid" ]]; then sudo kill "$(cat "$fixture_dir/sshd.pid")" || true; fi
  rm -rf "$fixture_dir"
}
trap cleanup EXIT
ssh-keygen -q -t ed25519 -N '' -f "$fixture_dir/client"
ssh-keygen -q -t ed25519 -N '' -f "$fixture_dir/host"
chmod 755 "$fixture_dir"
chmod 644 "$fixture_dir/client.pub"
cat > "$fixture_dir/sshd_config" <<CONFIG
Port 22222
ListenAddress 127.0.0.1
HostKey $fixture_dir/host
PidFile $fixture_dir/sshd.pid
AuthorizedKeysFile $fixture_dir/client.pub
StrictModes no
PasswordAuthentication no
KbdInteractiveAuthentication no
PubkeyAuthentication yes
UsePAM yes
AllowUsers $(id -un)
CONFIG
sudo mkdir -p /run/sshd
sudo /usr/sbin/sshd -f "$fixture_dir/sshd_config" -E "$fixture_dir/sshd.log"
mkdir -p "$HOME/.ssh"
chmod 700 "$HOME/.ssh"
ssh-keyscan -p 22222 127.0.0.1 >> "$HOME/.ssh/known_hosts" 2>/dev/null
export AIO_SSH_TEST_KEY="$fixture_dir/client"
export AIO_SSH_TEST_PORT=22222
uv run --no-sync python -m pytest tests/test_ssh_integration.py -q
