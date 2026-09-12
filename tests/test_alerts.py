from __future__ import annotations

import unittest
from unittest.mock import MagicMock

from security_cam.alerts import Alerter
from security_cam.config import Settings


class AlerterTests(unittest.TestCase):
    def test_local_only_does_not_use_twilio(self):
        settings = Settings(local_only=True, alert_cooldown_seconds=60)
        client = MagicMock()
        times = iter([100.0, 101.0])
        alerter = Alerter(settings, client=client, clock=lambda: next(times))
        self.assertTrue(alerter.send())
        client.messages.create.assert_not_called()

    def test_cooldown_suppresses_repeat_alerts(self):
        settings = Settings(
            local_only=False,
            alert_cooldown_seconds=60,
            twilio_whatsapp_to="whatsapp:+1",
            twilio_whatsapp_from="whatsapp:+2",
        )
        client = MagicMock()
        clock = MagicMock(side_effect=[10.0, 20.0, 80.0])
        alerter = Alerter(settings, client=client, clock=clock)
        self.assertTrue(alerter.send())
        self.assertFalse(alerter.send())
        self.assertTrue(alerter.send())
        self.assertEqual(client.messages.create.call_count, 2)

    def test_local_only_still_respects_cooldown(self):
        settings = Settings(local_only=True, alert_cooldown_seconds=30)
        clock = MagicMock(side_effect=[1.0, 10.0, 40.0])
        alerter = Alerter(settings, client=MagicMock(), clock=clock)
        self.assertTrue(alerter.send())
        self.assertFalse(alerter.send())
        self.assertTrue(alerter.send())


if __name__ == "__main__":
    unittest.main()
