from app.wasmtime_embedded_checker import check_email_wasmtime_embedded


def test_wasmtime_embedded_uses_allowlisted_host_api() -> None:
    result = check_email_wasmtime_embedded("user@example.com", "001")
    assert result.result == "OK"
    assert result.fuel_remaining < 20_000


def test_wasmtime_embedded_rejects_unknown_domain_or_code() -> None:
    assert check_email_wasmtime_embedded("user@other.test", "001").result == "NG"
    assert check_email_wasmtime_embedded("user@example.com", "999").result == "NG"
