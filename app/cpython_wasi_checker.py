"""Wasmtime + CPython WASI POC scaffold.

The real CPython WASI runtime is intentionally external/configured because no stable
small official binary is published with this repository. When configured, the POC
runs the rule in a WASI instance with a preopened temp directory only.
"""

from dataclasses import dataclass
import json
import os
from pathlib import Path
import tempfile
import textwrap
import time

import wasmtime

from app.email_checker import check_email as legacy_check_email


@dataclass(frozen=True)
class CPythonWasiResult:
    result: str
    elapsed_ms: float
    error: str | None = None
    used_runtime: bool = False


DEFAULT_RULE = """
def check(email):
    return "@" in email
"""


def _runtime_path() -> Path | None:
    raw = os.environ.get("CPYTHON_WASI_WASM")
    if not raw:
        return None
    path = Path(raw)
    return path if path.is_file() else None


def check_email_cpython_wasi(email: str, user_code: str = DEFAULT_RULE) -> CPythonWasiResult:
    runtime = _runtime_path()
    if runtime is None:
        return CPythonWasiResult(
            legacy_check_email(email, ""),
            0.0,
            "CPYTHON_WASI_WASM is not configured; used legacy checker fallback",
            False,
        )

    started = time.perf_counter()
    with tempfile.TemporaryDirectory(prefix="cpython-wasi-") as tmp:
        tmp_path = Path(tmp)
        (tmp_path / "input.json").write_text(json.dumps({"email": email}), encoding="utf-8")
        rule_source = f"""import json
data = json.load(open('/sandbox/input.json'))
email = data['email']
result = False
{user_code}
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
        store.set_fuel(50_000_000_000)
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
        module = wasmtime.Module.from_file(engine, str(runtime))
        try:
            instance = linker.instantiate(store, module)
            start = instance.exports(store).get("_start")
            if start is None:
                return CPythonWasiResult("NG", (time.perf_counter() - started) * 1000, "runtime has no _start", True)
            start(store)
        except Exception as exc:  # noqa: BLE001 - POC reports runtime failures as NG.
            err = stderr.read_text(encoding="utf-8") if stderr.exists() else ""
            return CPythonWasiResult("NG", (time.perf_counter() - started) * 1000, f"{exc}; {err}", True)

        try:
            data = json.loads(stdout.read_text(encoding="utf-8").strip().splitlines()[-1])
        except Exception as exc:  # noqa: BLE001
            err = stderr.read_text(encoding="utf-8") if stderr.exists() else ""
            return CPythonWasiResult("NG", (time.perf_counter() - started) * 1000, f"invalid output: {exc}; {err}", True)
        return CPythonWasiResult(data.get("result", "NG"), (time.perf_counter() - started) * 1000, None, True)
