# POC result: MicroPython on WASM

## Status

Partially implemented / blocked by runtime acquisition.

The branch contains `app/micropython_wasm_checker.py`, which can execute a configured MicroPython WASI/WASM runtime when `MICROPYTHON_WASM=/path/to/micropython.wasm` is set.
No stable, pinned server-side MicroPython WASI artifact was added to this repository, so `/check` falls back to the legacy checker in the default test environment.

## Tried

- Added a Wasmtime-based runner scaffold.
- Configured a preopened temp directory only for rule execution.
- Configured fuel and a smaller memory limit than CPython (`16 MiB`) to model the lightweight goal.

## Next steps

1. Choose a specific MicroPython WASM/WASI build source and pin checksums.
2. Verify CLI invocation semantics for executing `/sandbox/rule.py`.
3. Validate language subset compatibility against desired user rules.
4. Add runtime-available integration tests and latency/memory benchmarks.

## Sandbox / limits

- Timeout direction: Wasmtime fuel is configured; production should add subprocess wall-clock timeout.
- Memory limit: `Store.set_limits(memory_size=16 MiB)` is configured.
- Filesystem: only `/sandbox` is preopened.
- Host API allowlist: unresolved. MicroPython-compatible host calls likely need an explicit import/stdio protocol or generated bindings.

## OSS review

| OSS | License | Maintenance | Security | Fit |
|---|---|---|---|---|
| MicroPython | MIT | Mature project; WASM/WASI deployment story is less standardized than browser/demo builds | Smaller runtime and stdlib surface can reduce attack area, but artifact provenance must be pinned | Good fit for simple rules if CPython compatibility is not required |
| wasmtime / wasmtime-py | Apache-2.0 WITH LLVM-exception | Actively maintained by the Bytecode Alliance | Strong sandbox model; supports fuel and store limits | Good runtime layer for a WASI-compatible MicroPython binary |

## Findings

MicroPython remains promising for startup and memory, but runtime packaging and compatibility validation are the key blockers.
