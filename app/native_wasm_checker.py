"""Native WASM module POC for /check.

The module receives only primitive values derived by the host and returns 1/0.
This keeps the boundary small and leaves room to add allowlisted Host APIs later.
"""

from dataclasses import dataclass
import time

import wasmtime


@dataclass(frozen=True)
class NativeWasmResult:
    result: str
    elapsed_ms: float
    fuel_remaining: int


WAT_RULE = r"""
(module
  (func (export "check") (param $email_has_at i32) (param $code_is_001 i32) (result i32)
    local.get $email_has_at
    local.get $code_is_001
    i32.and)
)
"""


def _engine() -> wasmtime.Engine:
    config = wasmtime.Config()
    config.consume_fuel = True
    return wasmtime.Engine(config)


def check_email_native_wasm(email: str, code: str, *, fuel: int = 10_000) -> NativeWasmResult:
    engine = _engine()
    store = wasmtime.Store(engine)
    store.set_fuel(fuel)
    store.set_limits(memory_size=64 * 1024)
    module = wasmtime.Module(engine, WAT_RULE)
    instance = wasmtime.Instance(store, module, [])
    check = instance.exports(store)["check"]

    started = time.perf_counter()
    ok = check(store, int("@" in email), int(code == "001"))
    elapsed_ms = (time.perf_counter() - started) * 1000
    return NativeWasmResult(
        result="OK" if ok else "NG",
        elapsed_ms=elapsed_ms,
        fuel_remaining=store.get_fuel(),
    )
