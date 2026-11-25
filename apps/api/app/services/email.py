from __future__ import annotations

import html
import logging
from dataclasses import dataclass
from typing import Protocol

import httpx

from app.config import Settings, get_settings

logger = logging.getLogger(__name__)


class EmailNotConfiguredError(Exception):
    """Провайдер писем не настроен для текущего окружения."""


@dataclass(frozen=True)
class EmailMessage:
    to: str
    subject: str
    text: str
    html: str | None = None


class EmailSender(Protocol):
    async def send(self, message: EmailMessage) -> None: ...


class ConsoleEmailSender:
    async def send(self, message: EmailMessage) -> None:
        logger.info(
            "Письмо для %s\nТема: %s\n\n%s",
            message.to,
            message.subject,
            message.text,
        )


class UnisenderGoEmailSender:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def build_payload(self, message: EmailMessage) -> dict[str, object]:
        body: dict[str, str] = {"plaintext": message.text}
        if message.html:
            body["html"] = message.html

        return {
            "message": {
                "recipients": [{"email": message.to}],
                "body": body,
                "subject": message.subject,
                "from_email": self._settings.email_from,
                "from_name": self._settings.email_from_name,
                # Транзакционные ссылки (сброс пароля) не должны оборачиваться
                # в домен трекинга: если он недоступен, ссылка не открывается.
                "track_links": 0,
            }
        }

    async def send(self, message: EmailMessage) -> None:
        url = f"{self._settings.unisender_api_url.rstrip('/')}/email/send.json"
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.post(
                url,
                headers={"X-API-KEY": self._settings.unisender_api_key},
                json=self.build_payload(message),
            )
            response.raise_for_status()

        payload = response.json()
        if payload.get("status") != "success":
            raise RuntimeError("Unisender Go не принял письмо")


class ResendEmailSender:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def build_payload(self, message: EmailMessage) -> dict[str, object]:
        name = self._settings.email_from_name.strip()
        sender = f"{name} <{self._settings.email_from}>" if name else self._settings.email_from
        payload: dict[str, object] = {
            "from": sender,
            "to": [message.to],
            "subject": message.subject,
            "text": message.text,
        }
        if message.html:
            payload["html"] = message.html
        return payload

    async def send(self, message: EmailMessage) -> None:
        url = f"{self._settings.resend_api_url.rstrip('/')}/emails"
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.post(
                url,
                headers={"Authorization": f"Bearer {self._settings.resend_api_key}"},
                json=self.build_payload(message),
            )
            response.raise_for_status()

        if not response.json().get("id"):
            raise RuntimeError("Resend не принял письмо")


def get_email_sender(settings: Settings | None = None) -> EmailSender:
    current = settings or get_settings()
    if current.email_provider == "resend":
        if not current.resend_api_key or not current.email_from:
            raise EmailNotConfiguredError("Не заданы ключ Resend или адрес отправителя")
        return ResendEmailSender(current)

    if current.email_provider == "unisender":
        if not current.unisender_api_key or not current.email_from:
            raise EmailNotConfiguredError("Не заданы ключ Unisender Go или адрес отправителя")
        return UnisenderGoEmailSender(current)

    if current.is_local:
        return ConsoleEmailSender()

    raise EmailNotConfiguredError("Для production нужен реальный email-провайдер")


async def send_password_reset_email(
    sender: EmailSender,
    *,
    to: str,
    name: str,
    reset_url: str,
    ttl_minutes: int,
) -> None:
    safe_name = html.escape(name)
    safe_url = html.escape(reset_url, quote=True)
    await sender.send(
        EmailMessage(
            to=to,
            subject="Восстановление пароля — Levickaya Piano",
            text=(
                f"Здравствуйте, {name}!\n\n"
                "Вы запросили восстановление пароля в Levickaya Piano.\n"
                f"Ссылка действует {ttl_minutes} минут:\n{reset_url}\n\n"
                "Если вы не запрашивали восстановление, просто проигнорируйте письмо."
            ),
            html=(
                f"<p>Здравствуйте, {safe_name}!</p>"
                "<p>Вы запросили восстановление пароля в Levickaya Piano.</p>"
                f"<p><a href=\"{safe_url}\">Задать новый пароль</a></p>"
                f"<p>Ссылка действует {ttl_minutes} минут. "
                "Если вы не запрашивали восстановление, просто проигнорируйте письмо.</p>"
            ),
        )
    )
