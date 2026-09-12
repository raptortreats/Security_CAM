from __future__ import annotations

import time
from typing import Any, Protocol

from security_cam.config import Settings


class MessageClient(Protocol):
    messages: Any


class Alerter:
    """WhatsApp alerts via Twilio, or a no-op logger in local-only mode."""

    def __init__(
        self,
        settings: Settings,
        client: MessageClient | None = None,
        clock=time.time,
    ) -> None:
        self.settings = settings
        self._client = client
        self._clock = clock
        self._last_alert_time: float | None = None

    def send(self, body: str = "Intruder Alert") -> bool:
        now = self._clock()
        if (
            self._last_alert_time is not None
            and now - self._last_alert_time < self.settings.alert_cooldown_seconds
        ):
            return False

        if self.settings.local_only:
            print(f"[local-only] {body} (WhatsApp disabled)")
            self._last_alert_time = now
            return True

        client = self._client or self._build_client()
        client.messages.create(
            to=self.settings.twilio_whatsapp_to,
            from_=self.settings.twilio_whatsapp_from,
            body=body,
        )
        self._last_alert_time = now
        return True

    def _build_client(self) -> MessageClient:
        from twilio.rest import Client

        return Client(self.settings.twilio_account_sid, self.settings.twilio_auth_token)
