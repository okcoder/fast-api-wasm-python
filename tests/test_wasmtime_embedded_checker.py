from app.wasmtime_embedded_checker import check_email_wasmtime_embedded

PYTHON_CODE = 'def check(email):\n    return "@" in email'
STRICT_PYTHON_CODE = 'def check(email):\n    return "@" in email and email.endswith("example.com")'


def test_wasmtime_embedded_falls_back_when_runtime_not_configured(monkeypatch) -> None:
    monkeypatch.delenv("WASMTIME_EMBEDDED_PYTHON_WASM", raising=False)
    monkeypatch.delenv("CPYTHON_WASI_WASM", raising=False)
    result = check_email_wasmtime_embedded("user@example.com", PYTHON_CODE)
    assert result.result == "OK"
    assert result.used_runtime is False


def test_wasmtime_embedded_runs_python_code_when_runtime_is_configured(monkeypatch) -> None:
    monkeypatch.setenv("WASMTIME_EMBEDDED_PYTHON_WASM", "vendor/wasmtime-embedded-python/python.wasm")
    result = check_email_wasmtime_embedded("user@example.com", PYTHON_CODE)
    assert result.result == "OK"
    assert result.used_runtime is True
    assert result.error is None
    assert result.fuel_remaining is not None


def test_wasmtime_embedded_returns_ng_for_rule_false(monkeypatch) -> None:
    monkeypatch.setenv("WASMTIME_EMBEDDED_PYTHON_WASM", "vendor/wasmtime-embedded-python/python.wasm")
    result = check_email_wasmtime_embedded("example.com", PYTHON_CODE)
    assert result.result == "NG"
    assert result.used_runtime is True
    assert result.error is None


def test_wasmtime_embedded_accepts_request_python_code(monkeypatch) -> None:
    monkeypatch.setenv("WASMTIME_EMBEDDED_PYTHON_WASM", "vendor/wasmtime-embedded-python/python.wasm")
    assert check_email_wasmtime_embedded("user@example.com", STRICT_PYTHON_CODE).result == "OK"
    assert check_email_wasmtime_embedded("user@example.org", STRICT_PYTHON_CODE).result == "NG"
