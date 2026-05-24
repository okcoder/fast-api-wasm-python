# POC result: Native WASM module

## Status

Implemented. `/check` invokes an embedded native WASM module through `wasmtime-py`.
The POC passes primitive values (`email_has_at`, `code_is_001`) into WASM and returns `OK`/`NG`.

## Sandbox / limits

- Timeout direction: Wasmtime fuel is enabled; epoch interruption can be added for wall-clock deadlines.
- Memory limit: `Store.set_limits(memory_size=64 KiB)` is configured for the instance.
- Host API allowlist: no host function is imported yet. Future host APIs should be added as explicit imports only.

## OSS review

| OSS | License | Maintenance | Security | Fit |
|---|---|---|---|---|
| wasmtime / wasmtime-py | Apache-2.0 WITH LLVM-exception | Actively maintained by the Bytecode Alliance | Strong sandbox model; fuel and store limits are available | Excellent for native WASM isolation/performance baseline, but does not satisfy Python-authoring UX |

## Findings

This is the fastest and smallest baseline, but it requires rules to be compiled to WASM or represented by a fixed ABI.
It is useful as an upper-bound comparison for isolation and performance.
