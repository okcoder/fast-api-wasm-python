from collections.abc import Callable

type CheckRule = Callable[[str, str], bool]


def has_at_mark(email: str, code: str) -> bool:
    return "@" in email


_check_rules: list[CheckRule] = [has_at_mark]


def register_check_rule(rule: CheckRule) -> None:
    _check_rules.append(rule)


def unregister_check_rule(rule: CheckRule) -> None:
    _check_rules.remove(rule)


def check_email(email: str, code: str) -> str:
    return "OK" if all(rule(email, code) for rule in _check_rules) else "NG"
