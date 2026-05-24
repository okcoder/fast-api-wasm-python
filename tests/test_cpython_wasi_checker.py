from app.cpython_wasi_checker import check_email_cpython_wasi


def test_cpython_wasi_falls_back_when_runtime_not_configured(monkeypatch) -> None:
    monkeypatch.delenv("CPYTHON_WASI_WASM", raising=False)
    result = check_email_cpython_wasi("user@example.com", "001")
    assert result.result == "OK"
    assert result.used_runtime is False
    assert "CPYTHON_WASI_WASM" in (result.error or "")
