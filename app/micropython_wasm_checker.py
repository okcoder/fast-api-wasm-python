"""MicroPython-on-WASM POC scaffold.

Runs a configured MicroPython WASI/WASM binary when available. The fallback keeps
/check functional while documenting that runtime acquisition is the blocker.
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
class MicroPythonWasmResult:
    result: str
    elapsed_ms: float
    error: str | None = None
    used_runtime: bool = False


DEFAULT_RULE = """
result = ("@" in email) and (code == "001")
"""


def _runtime_path() -> Path | None:
    raw = os.environ.get("MICROPYTHON_WASM")
    if not raw:
        return None
    path = Path(raw)
    return path if path.is_file() else None


def check_email_micropython_wasm(email: str, code: str, user_code: str = DEFAULT_RULE) -> MicroPythonWasmResult:
    runtime = _runtime_path()
    if runtime is None:
        return MicroPythonWasmResult(
            legacy_check_email(email, code),
            0.0,
            "MICROPYTHON_WASM is not configured; used legacy checker fallback",
            False,
        )

    started = time.perf_counter()
    with tempfile.TemporaryDirectory(prefix="micropython-wasm-") as tmp:
        tmp_path = Path(tmp)
        rule = tmp_path / "rule.py"
        stdout = tmp_path / "stdout.txt"
        stderr = tmp_path / "stderr.txt"
        rule.write_text(
            textwrap.dedent(
                f"""
                email = {email!r}
                code = {code!r}
                result = False
                {textwrap.indent(user_code, '                ')}
                import json
                print(json.dumps({{'result': 'OK' if result else 'NG'}}))
                """
            ),
            encoding="utf-8",
        )

        config = wasmtime.Config()
        config.consume_fuel = True
        engine = wasmtime.Engine(config)
        store = wasmtime.Store(engine)
        store.set_fuel(1_000_000)
        store.set_limits(memory_size=16 * 1024 * 1024)
        wasi = wasmtime.WasiConfig()
        wasi.argv = (str(runtime), "/sandbox/rule.py")
        wasi.preopen_dir(str(tmp_path), "/sandbox")
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
                return MicroPythonWasmResult("NG", (time.perf_counter() - started) * 1000, "runtime has no _start", True)
            start(store)
            data = json.loads(stdout.read_text(encoding="utf-8").strip().splitlines()[-1])
            return MicroPythonWasmResult(data.get("result", "NG"), (time.perf_counter() - started) * 1000, None, True)
        except Exception as exc:  # noqa: BLE001 - POC returns runtime errors as NG.
            err = stderr.read_text(encoding="utf-8") if stderr.exists() else ""
            return MicroPythonWasmResult("NG", (time.perf_counter() - started) * 1000, f"{exc}; {err}", True)
