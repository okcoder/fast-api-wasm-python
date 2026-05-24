from app.pyodide_node_checker import check_email_pyodide_node


def test_pyodide_node_checker_ok() -> None:
    assert check_email_pyodide_node("user@example.com", "001").result == "OK"


def test_pyodide_node_checker_can_execute_request_code() -> None:
    user_code = 'result = email.endswith("@example.com") and code == "ABC" and is_company_domain(email)'
    assert check_email_pyodide_node("user@example.com", "ABC", user_code).result == "OK"
    assert check_email_pyodide_node("user@other.test", "ABC", user_code).result == "NG"
