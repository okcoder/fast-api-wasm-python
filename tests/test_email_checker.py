from app.email_checker import check_email, register_check_rule, unregister_check_rule


def test_check_email_returns_ok_when_email_contains_at_mark() -> None:
    assert check_email("user@example.com", "001") == "OK"


def test_check_email_returns_ng_when_email_does_not_contain_at_mark() -> None:
    assert check_email("example.com", "001") == "NG"


def test_check_email_can_be_extended_with_external_rule() -> None:
    def code_must_be_001(email: str, code: str) -> bool:
        return code == "001"

    register_check_rule(code_must_be_001)
    try:
        assert check_email("user@example.com", "001") == "OK"
        assert check_email("user@example.com", "999") == "NG"
    finally:
        unregister_check_rule(code_must_be_001)
