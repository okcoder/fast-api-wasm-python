from app.native_wasm_checker import check_email_native_wasm


def test_native_wasm_checker_ok() -> None:
    result = check_email_native_wasm("user@example.com", "001")
    assert result.result == "OK"
    assert result.fuel_remaining < 10_000


def test_native_wasm_checker_ng() -> None:
    assert check_email_native_wasm("example.com", "001").result == "NG"
    assert check_email_native_wasm("user@example.com", "999").result == "NG"
