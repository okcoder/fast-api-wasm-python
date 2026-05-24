# POC result: Pyodide + Node runner

## Status

Implemented. FastAPI calls a subprocess Node runner that loads Pyodide, executes Python user code, and returns `OK`/`NG` JSON.
The default rule checks `email`, `code`, and a bridged Host API `is_company_domain(email)`.

## Sandbox / limits

- Timeout: Python wrapper uses `subprocess.run(..., timeout=...)`.
- Memory: Node is started with `--max-old-space-size=128` for a coarse heap cap.
- Host API allowlist: only `is_company_domain` is exposed through the JS/Python bridge.
- Isolation: runner is a subprocess, so failures are more contained than in-process execution.

## OSS review

| OSS | License | Maintenance | Security | Fit |
|---|---|---|---|---|
| Pyodide | MPL-2.0 | Actively maintained by the Pyodide community | Browser/WASM isolation model; in Node, combine subprocess timeout and explicit bridge limits | Strong Python UX and Host API bridge fit, but adds Node and large runtime assets |
| Node.js | MIT | Actively maintained LTS/current releases | Requires normal subprocess hardening and dependency management | Acceptable if bundling Node in the existing container is operationally allowed |

## Findings

Host API integration is the most natural among the Python-compatible options.
The primary drawbacks are startup latency, image size, and operational complexity from adding Node/Pyodide.
