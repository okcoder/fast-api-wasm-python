"""wasmtime-py embedded POC with an explicit Host API allowlist."""

from dataclasses import dataclass
import time

import wasmtime


@dataclass(frozen=True)
class WasmtimeEmbeddedResult:
    result: str
    elapsed_ms: float
    fuel_remaining: int


WAT_RULE = r"""
(module
  (import "host" "is_company_domain" (func $is_company_domain (param i32) (result i32)))
  (func (export "check") (param $email_has_at i32) (param $domain_id i32) (param $code_is_001 i32) (result i32)
    local.get $email_has_at
    local.get $domain_id
    call $is_company_domain
    i32.and
    local.get $code_is_001
    i32.and)
)
"""

_DOMAIN_IDS = {
    "example.com": 1,
    "company.test": 2,
}
_ALLOWED_COMPANY_DOMAIN_IDS = {1}


def _domain_id(email: str) -> int:
    if "@" not in email:
        return 0
    return _DOMAIN_IDS.get(email.rsplit("@", 1)[1].lower(), 0)


def _engine() -> wasmtime.Engine:
    config = wasmtime.Config()
    config.consume_fuel = True
    return wasmtime.Engine(config)


def check_email_wasmtime_embedded(email: str, code: str, *, fuel: int = 20_000) -> WasmtimeEmbeddedResult:
    engine = _engine()
    store = wasmtime.Store(engine)
    store.set_fuel(fuel)
    store.set_limits(memory_size=128 * 1024)

    def is_company_domain(domain_id: int) -> int:
        return int(domain_id in _ALLOWED_COMPANY_DOMAIN_IDS)

    host_func = wasmtime.Func(
        store,
        wasmtime.FuncType([wasmtime.ValType.i32()], [wasmtime.ValType.i32()]),
        is_company_domain,
    )
    module = wasmtime.Module(engine, WAT_RULE)
    instance = wasmtime.Instance(store, module, [host_func])
    check = instance.exports(store)["check"]

    started = time.perf_counter()
    ok = check(store, int("@" in email), _domain_id(email), int(code == "001"))
    elapsed_ms = (time.perf_counter() - started) * 1000
    return WasmtimeEmbeddedResult("OK" if ok else "NG", elapsed_ms, store.get_fuel())
