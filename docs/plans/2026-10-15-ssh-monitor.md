# SSH monitoring implementation plan

**Goal:** A small, agentless Linux server dashboard configured with SSH aliases.

**Architecture:** Python asyncio invokes the local OpenSSH client, preserving SSH config, key agents, known hosts and jump hosts. A fixed read-only shell probe reports Linux metrics. An aiohttp service caches concurrent polls and serves a static dashboard. Documentation and a clearly labeled demo are published to GitHub Pages; SSH credentials stay on the control machine.

**Stack:** Python 3.11+, aiohttp, PyYAML, OpenSSH, React, TypeScript, Vite, Sphinx + MyST (updated by the uv/release migration).

## Delivery steps

1. Add failing tests for minimal YAML configuration, validation, Linux probe parsing, subprocess timeouts, partial host failures and API behavior.
2. Implement separate configuration, probe, SSH transport, monitor, HTTP service and CLI modules. Add init, check and serve commands, a bundled dashboard, and optional API token protection.
3. Replace the scaffold with a responsive dashboard: explicit demo mode, search and group filters, online/offline status, CPU/memory/disk/GPU, network rates, history and connection errors. Produce relative static assets for local serving and GitHub Pages subpaths.
4. Replace template documentation with Chinese quick start, configuration reference, SSH setup, metrics, API, deployment and troubleshooting. Document the unavailable reference repository and intended relationship without claiming compatibility.
5. Update packaging, development dependencies, build scripts and GitHub Actions. Test Python 3.11–3.14, lint/typecheck/test/build the frontend, build and install a wheel with bundled assets, and build docs strictly. Deploy Pages only from the default branch or manual dispatch.
6. Run tests and builds, exercise the real SSH probe against a local Linux fixture if available, and review the complete change before reporting results.

## Acceptance criteria

- `aio-server-status init`, edit aliases, `aio-server-status check`, `aio-server-status serve` provides a practical setup flow.
- Targets require Linux, sshd, standard shell tools and a trusted host key; no remote Python, agent, sudo, database or extra listening port.
- Polling is bounded and concurrent; failed hosts and stale browser snapshots are visibly distinct.
- SSH credentials never enter the frontend or Pages artifacts.
- A built wheel serves the frontend without a Node runtime.
- CI validates source, frontend, distributions and docs; Pages hosts docs plus a demo with synthetic data.
