from app.cpython_wasi_checker import check_email_cpython_wasi

PYTHON_CODE = 'def check(email):\n    return "@" in email'


def test_cpython_wasi_falls_back_when_runtime_not_configured(monkeypatch) -> None:
    monkeypatch.delenv("CPYTHON_WASI_WASM", raising=False)
    result = check_email_cpython_wasi("user@example.com", PYTHON_CODE)
    assert result.result == "OK"
    assert result.used_runtime is False
    assert "CPYTHON_WASI_WASM" in (result.error or "")


def test_cpython_wasi_runs_when_runtime_is_configured(monkeypatch) -> None:
    monkeypatch.setenv("CPYTHON_WASI_WASM", "vendor/cpython-wasi/python.wasm")
    result = check_email_cpython_wasi("user@example.com", PYTHON_CODE)
    assert result.result == "OK"
    assert result.used_runtime is True
    assert result.error is None


def test_cpython_wasi_returns_ng_for_rule_false(monkeypatch) -> None:
    monkeypatch.setenv("CPYTHON_WASI_WASM", "vendor/cpython-wasi/python.wasm")
    result = check_email_cpython_wasi("example.com", PYTHON_CODE)
    assert result.result == "NG"
    assert result.used_runtime is True
    assert result.error is None
