from app.micropython_wasm_checker import check_email_micropython_wasm


def test_micropython_wasm_falls_back_when_runtime_not_configured(monkeypatch) -> None:
    monkeypatch.delenv("MICROPYTHON_WASM", raising=False)
    result = check_email_micropython_wasm("user@example.com", "001")
    assert result.result == "OK"
    assert result.used_runtime is False
    assert "MICROPYTHON_WASM" in (result.error or "")
