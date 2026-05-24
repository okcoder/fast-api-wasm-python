"""Pyodide + Node runner POC for executing Python user rules."""

from dataclasses import dataclass
import json
from pathlib import Path
import shutil
import subprocess
import time


@dataclass(frozen=True)
class PyodideNodeResult:
    result: str
    elapsed_ms: float
    error: str | None = None


DEFAULT_RULE = """
result = ("@" in email) and (code == "001") and is_company_domain(email)
"""


def check_email_pyodide_node(
    email: str,
    code: str,
    user_code: str = DEFAULT_RULE,
    *,
    timeout_seconds: float = 5.0,
) -> PyodideNodeResult:
    node = shutil.which("node")
    if node is None:
        return PyodideNodeResult("NG", 0.0, "node executable is not available")

    runner = Path(__file__).resolve().parents[1] / "runners" / "pyodide_check_runner.mjs"
    payload = json.dumps({"email": email, "code": code, "user_code": user_code})
    started = time.perf_counter()
    try:
        completed = subprocess.run(
            [node, "--max-old-space-size=128", str(runner)],
            input=payload,
            text=True,
            capture_output=True,
            timeout=timeout_seconds,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return PyodideNodeResult("NG", (time.perf_counter() - started) * 1000, "timeout")

    elapsed_ms = (time.perf_counter() - started) * 1000
    if completed.returncode != 0:
        return PyodideNodeResult("NG", elapsed_ms, completed.stderr.strip() or "node runner failed")
    try:
        data = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        return PyodideNodeResult("NG", elapsed_ms, f"invalid runner output: {exc}")
    return PyodideNodeResult(data.get("result", "NG"), elapsed_ms, data.get("error"))
