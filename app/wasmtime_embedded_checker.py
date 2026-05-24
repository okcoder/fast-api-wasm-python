"""wasmtime-py embedded POC that runs request Python code in CPython WASI."""

from dataclasses import dataclass
import json
import os
from pathlib import Path
import tempfile
import time

import wasmtime

from app.email_checker import check_email as legacy_check_email


@dataclass(frozen=True)
class WasmtimeEmbeddedResult:
    result: str
    elapsed_ms: float
    error: str | None = None
    used_runtime: bool = False
    fuel_remaining: int | None = None


DEFAULT_CODE = """
def check(email):
    return "@" in email
"""


def _runtime_path() -> Path | None:
    raw = os.environ.get("WASMTIME_EMBEDDED_PYTHON_WASM")
    if not raw:
        raw = os.environ.get("CPYTHON_WASI_WASM")
    if not raw:
        return None
    path = Path(raw)
    return path if path.is_file() else None


def check_email_wasmtime_embedded(
    email: str,
    code: str = DEFAULT_CODE,
    *,
    fuel: int = 50_000_000_000,
) -> WasmtimeEmbeddedResult:
    runtime = _runtime_path()
    if runtime is None:
        return WasmtimeEmbeddedResult(
            legacy_check_email(email, ""),
            0.0,
            "WASMTIME_EMBEDDED_PYTHON_WASM or CPYTHON_WASI_WASM is not configured; used legacy checker fallback",
            False,
            None,
        )

    started = time.perf_counter()
    with tempfile.TemporaryDirectory(prefix="wasmtime-embedded-python-") as tmp:
        tmp_path = Path(tmp)
        (tmp_path / "input.json").write_text(json.dumps({"email": email}), encoding="utf-8")
        rule_source = f"""import json
data = json.load(open('/sandbox/input.json'))
email = data['email']
result = False
{code}
try:
    result = check(email)
except NameError:
    pass
print(json.dumps({{'result': 'OK' if result else 'NG'}}))
"""
        (tmp_path / "rule.py").write_text(rule_source, encoding="utf-8")
        stdout = tmp_path / "stdout.txt"
        stderr = tmp_path / "stderr.txt"

        config = wasmtime.Config()
        config.consume_fuel = True
        engine = wasmtime.Engine(config)
        store = wasmtime.Store(engine)
        store.set_fuel(fuel)
        store.set_limits(memory_size=256 * 1024 * 1024)

        wasi = wasmtime.WasiConfig()
        wasi.argv = (str(runtime), "-S", "/sandbox/rule.py")
        wasi.preopen_dir(str(tmp_path), "/sandbox")
        wasi.preopen_dir(str(runtime.parent), "/runtime")
        wasi.env = (("PYTHONHOME", "/runtime"), ("PYTHONPATH", "/runtime/lib/python3.13"))
        wasi.stdout_file = str(stdout)
        wasi.stderr_file = str(stderr)
        store.set_wasi(wasi)

        linker = wasmtime.Linker(engine)
        linker.define_wasi()

        try:
            module = wasmtime.Module.from_file(engine, str(runtime))
            instance = linker.instantiate(store, module)
            start = instance.exports(store).get("_start")
            if start is None:
                return WasmtimeEmbeddedResult("NG", (time.perf_counter() - started) * 1000, "runtime has no _start", True, store.get_fuel())
            start(store)
        except Exception as exc:  # noqa: BLE001 - POC reports runtime failures as NG.
            err = stderr.read_text(encoding="utf-8") if stderr.exists() else ""
            return WasmtimeEmbeddedResult("NG", (time.perf_counter() - started) * 1000, f"{exc}; {err}", True, store.get_fuel())

        try:
            data = json.loads(stdout.read_text(encoding="utf-8").strip().splitlines()[-1])
        except Exception as exc:  # noqa: BLE001
            err = stderr.read_text(encoding="utf-8") if stderr.exists() else ""
            return WasmtimeEmbeddedResult("NG", (time.perf_counter() - started) * 1000, f"invalid output: {exc}; {err}", True, store.get_fuel())
        return WasmtimeEmbeddedResult(data.get("result", "NG"), (time.perf_counter() - started) * 1000, None, True, store.get_fuel())
