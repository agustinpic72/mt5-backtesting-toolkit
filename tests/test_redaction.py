from __future__ import annotations

try:
    from mt5_backtesting_toolkit.security.redaction import redact_mapping, redact_text
except ImportError:
    redact_mapping = None  # type: ignore[assignment]
    redact_text = None  # type: ignore[assignment]


def test_redaction_removes_credentials_and_personal_paths() -> None:
    assert redact_text is not None, "redaction is not implemented"
    source = (
        "token=abc123 password=hunter2 "
        r"C:\Users\PrivateName\terminal64.exe "
        "/home/privateuser/reports/result.html"
    )

    redacted = redact_text(source)

    for secret in ("abc123", "hunter2", "PrivateName", "privateuser"):
        assert secret not in redacted
    assert "[REDACTED:" in redacted


def test_redaction_recurses_and_redacts_secret_keys() -> None:
    assert redact_mapping is not None, "mapping redaction is not implemented"
    value = {
        "account": "DEMO-001",
        "nested": {"api_key": "private-value", "note": "safe"},
        "items": [{"password": "other-private-value"}],
    }

    redacted = redact_mapping(value)

    assert redacted["account"] == "DEMO-001"
    assert redacted["nested"]["api_key"] == "[REDACTED:SECRET]"
    assert redacted["items"][0]["password"] == "[REDACTED:SECRET]"  # noqa: S105
