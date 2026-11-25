import pytest

from app.config import Settings
from app.services.email import (
    ConsoleEmailSender,
    EmailMessage,
    EmailNotConfiguredError,
    ResendEmailSender,
    UnisenderGoEmailSender,
    get_email_sender,
)


def test_unisender_payload() -> None:
    settings = Settings(
        email_provider="unisender",
        email_from="no-reply@example.com",
        email_from_name="Levickaya Piano",
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
    assert message["track_links"] == 0


def test_resend_payload() -> None:
    settings = Settings(
        email_provider="resend",
        email_from="noreply@levickaya.ru",
        email_from_name="Levickaya Piano",
        resend_api_key="re_test",
    )
    sender = ResendEmailSender(settings)
    payload = sender.build_payload(
        EmailMessage(
            to="student@example.com",
            subject="Тема",
            text="Текст",
            html="<p>Текст</p>",
        )
    )

    assert payload == {
        "from": "Levickaya Piano <noreply@levickaya.ru>",
        "to": ["student@example.com"],
        "subject": "Тема",
        "text": "Текст",
        "html": "<p>Текст</p>",
    }
    assert isinstance(get_email_sender(settings), ResendEmailSender)


def test_resend_requires_key() -> None:
    with pytest.raises(EmailNotConfiguredError):
        get_email_sender(Settings(email_provider="resend", email_from="noreply@levickaya.ru"))


def test_local_uses_console_sender() -> None:
    sender = get_email_sender(Settings(environment="local"))
    assert isinstance(sender, ConsoleEmailSender)


def test_production_requires_provider() -> None:
    with pytest.raises(EmailNotConfiguredError):
        get_email_sender(Settings(environment="production", email_provider="console"))
