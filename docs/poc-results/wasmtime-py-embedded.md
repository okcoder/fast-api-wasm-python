# POC result: wasmtime-py embedded

## Status

Implemented. FastAPI calls `wasmtime-py` in-process and executes an embedded WAT module.
The module imports one explicit host function, `host.is_company_domain(domain_id)`, to model a future allowlisted Host API.

## Sandbox / limits

- Timeout direction: Wasmtime fuel is enabled; epoch interruption can be layered on for wall-clock cancellation.
- Memory limit: `Store.set_limits(memory_size=128 KiB)` is configured.
- Host API allowlist: host imports are explicitly constructed. User/WASM code cannot import arbitrary Python modules.

## OSS review

| OSS | License | Maintenance | Security | Fit |
|---|---|---|---|---|
| wasmtime / wasmtime-py | Apache-2.0 WITH LLVM-exception | Actively maintained by the Bytecode Alliance | Strong WASM sandbox; supports fuel and resource limits | Very good for quick in-container POC; production should consider subprocess isolation to reduce FastAPI blast radius |

## Findings

This path is operationally simple because it remains inside the existing Python container.
The main risk is embedding the runtime in the FastAPI process; a separate runner process is safer for production.
