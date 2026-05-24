# POC result: Wasmtime + CPython WASI

## Status

Partially implemented / blocked by runtime packaging.

The branch contains `app/cpython_wasi_checker.py`, which can run a CPython WASI `python.wasm` when `CPYTHON_WASI_WASM=/path/to/python.wasm` is provided.
In this environment no pinned CPython WASI binary was safely committed to the repo, so `/check` falls back to the legacy checker and reports the missing runtime in the structured result.

## Tried

- Added `wasmtime-py` and a WASI runner scaffold.
- Configured a preopened temp directory only (`/sandbox`) for input and rule files.
- Configured fuel and memory limits in `wasmtime.Store`.
- Checked current CPython WASI distribution state. Python.org discussion links point to unofficial `brettcannon/cpython-wasi-build` releases, not a small stable official artifact suitable to vendor in this repo.

## Next steps

1. Pin a specific CPython WASI release artifact and checksum in a fetch script.
2. Add a cache directory outside git for the runtime and standard library.
3. Verify `argv`, `PYTHONPATH`, stdlib layout, and stdout JSON protocol.
4. Add a no-fallback integration test guarded by runtime availability.

## Sandbox / limits

- Timeout direction: Wasmtime fuel is configured; add epoch interruption or subprocess wall-clock timeout for production.
- Memory limit: `Store.set_limits(memory_size=64 MiB)` is configured.
- Filesystem: only a temporary `/sandbox` directory is preopened.
- Host API allowlist: not solved yet for natural Python calls. A JSON/stdio protocol or WASI import bridge should be evaluated.

## OSS review

| OSS | License | Maintenance | Security | Fit |
|---|---|---|---|---|
| CPython WASI | Python Software Foundation License | WASI support exists but binary distribution is still evolving | Runs under WASI with explicit preopens; stdlib surface still needs review | Best Python compatibility candidate, but highest packaging and startup-cost risk |
| wasmtime / wasmtime-py | Apache-2.0 WITH LLVM-exception | Actively maintained by the Bytecode Alliance | Strong sandbox model; supports fuel and store limits | Good runtime layer for CPython WASI once packaging is pinned |

## Sources consulted

- Python.org discussion: WASI releases for CPython 3.11.9 and 3.12.10.
- `brettcannon/cpython-wasi-build` unofficial release references from that discussion.
