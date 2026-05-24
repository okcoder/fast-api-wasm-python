from app.micropython_wasm_checker import check_email_micropython_wasm

PYTHON_CODE = 'def check(email):\n    return "@" in email'
STRICT_PYTHON_CODE = 'def check(email):\n    return "@" in email and email.endswith(".com")'


def test_micropython_wasm_falls_back_when_runtime_not_configured(monkeypatch) -> None:
    monkeypatch.delenv("MICROPYTHON_WASM", raising=False)
    result = check_email_micropython_wasm("user@example.com", PYTHON_CODE)
    assert result.result == "OK"
    assert result.used_runtime is False
    assert "MICROPYTHON_WASM" in (result.error or "")


def test_micropython_wasm_runs_when_runtime_is_configured(monkeypatch) -> None:
    monkeypatch.setenv("MICROPYTHON_WASM", "vendor/micropython-wasm/micropython.wasm")
    result = check_email_micropython_wasm("user@example.com", PYTHON_CODE)
    assert result.result == "OK"
    assert result.used_runtime is True
    assert result.error is None


def test_micropython_wasm_returns_ng_for_rule_false(monkeypatch) -> None:
    monkeypatch.setenv("MICROPYTHON_WASM", "vendor/micropython-wasm/micropython.wasm")
    result = check_email_micropython_wasm("example.com", PYTHON_CODE)
    assert result.result == "NG"
    assert result.used_runtime is True
    assert result.error is None


def test_micropython_wasm_accepts_result_variable_style(monkeypatch) -> None:
    monkeypatch.setenv("MICROPYTHON_WASM", "vendor/micropython-wasm/micropython.wasm")
    result = check_email_micropython_wasm("user@example.com", 'result = email.endswith(".com")')
    assert result.result == "OK"
    assert result.used_runtime is True
    assert result.error is None
