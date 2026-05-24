"""MicroPython-on-WASM POC scaffold.

Runs a configured MicroPython WASI/WASM binary when available. The fallback keeps
/check functional while documenting that runtime acquisition is the blocker.
"""

from dataclasses import dataclass
import json
import os
import subprocess
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
def check(email):
    return "@" in email
"""


def _runtime_path() -> Path | None:
    raw = os.environ.get("MICROPYTHON_WASM")
    if not raw:
        return None
    path = Path(raw)
    return path if path.is_file() else None


def _node_runner_path(runtime: Path) -> Path | None:
    mjs = runtime.with_name("micropython.mjs")
    runner = Path(__file__).resolve().parent.parent / "scripts" / "micropython_wasm_runner.mjs"
    return runner if mjs.is_file() and runner.is_file() else None


def _run_with_node(runtime: Path, email: str, user_code: str, started: float) -> MicroPythonWasmResult:
    runner = _node_runner_path(runtime)
    if runner is None:
        return MicroPythonWasmResult("NG", (time.perf_counter() - started) * 1000, "micropython.mjs or node runner is missing", True)
    mjs = runtime.with_name("micropython.mjs")
    try:
        completed = subprocess.run(
            ["node", str(runner), str(mjs), str(runtime), email, user_code],
            check=False,
            capture_output=True,
            text=True,
            timeout=2.0,
            env={"PATH": os.environ.get("PATH", "")},
        )
        payload = json.loads(completed.stdout or "{}")
        error = payload.get("error")
        if completed.returncode != 0 and error is None:
            error = completed.stderr or "node runner failed"
        return MicroPythonWasmResult(payload.get("result", "NG"), (time.perf_counter() - started) * 1000, error, True)
    except subprocess.TimeoutExpired:
        return MicroPythonWasmResult("NG", (time.perf_counter() - started) * 1000, "node runner timeout", True)
    except Exception as exc:  # noqa: BLE001 - POC returns runtime errors as NG.
        return MicroPythonWasmResult("NG", (time.perf_counter() - started) * 1000, str(exc), True)


def check_email_micropython_wasm(email: str, user_code: str = DEFAULT_RULE) -> MicroPythonWasmResult:
    runtime = _runtime_path()
    if runtime is None:
        return MicroPythonWasmResult(
            legacy_check_email(email, ""),
            0.0,
            "MICROPYTHON_WASM is not configured; used legacy checker fallback",
            False,
        )

    started = time.perf_counter()
    if _node_runner_path(runtime) is not None:
        return _run_with_node(runtime, email, user_code, started)
    with tempfile.TemporaryDirectory(prefix="micropython-wasm-") as tmp:
        tmp_path = Path(tmp)
        rule = tmp_path / "rule.py"
        stdout = tmp_path / "stdout.txt"
        stderr = tmp_path / "stderr.txt"
        rule.write_text(
            textwrap.dedent(
                f"""
                email = {email!r}
                result = False
                {textwrap.indent(user_code, '                ')}
                try:
                    result = check(email)
                except NameError:
                    pass
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
