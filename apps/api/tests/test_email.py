import pytest

from app.config import Settings
from app.services.email import (
    ConsoleEmailSender,
    EmailMessage,
    EmailNotConfiguredError,
    UnisenderGoEmailSender,
    get_email_sender,
)


def test_unisender_payload() -> None:
    settings = Settings(
        email_provider="unisender",
        email_from="no-reply@example.com",
        email_from_name="Piano School",
        unisender_api_key="test-key",
    )
    sender = UnisenderGoEmailSender(settings)
    payload = sender.build_payload(
        EmailMessage(
            to="student@example.com",
            subject="Тема",
            text="Текст",
            html="<p>Текст</p>",
        )
    )

    message = payload["message"]
    assert isinstance(message, dict)
    assert message["recipients"] == [{"email": "student@example.com"}]
    assert message["from_email"] == "no-reply@example.com"
    assert message["body"] == {"plaintext": "Текст", "html": "<p>Текст</p>"}


def test_local_uses_console_sender() -> None:
    sender = get_email_sender(Settings(environment="local"))
    assert isinstance(sender, ConsoleEmailSender)


def test_production_requires_provider() -> None:
    with pytest.raises(EmailNotConfiguredError):
        get_email_sender(Settings(environment="production", email_provider="console"))
