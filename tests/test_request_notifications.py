import unittest
from unittest.mock import ANY, patch

import email_sender
import server


class RequestNotificationTests(unittest.TestCase):
    def setUp(self):
        self.client = server.app.test_client()

    def test_email_notification_is_sent_for_every_supported_country(self):
        for country in ("russia", "usa", "uk"):
            with self.subTest(country=country), \
                    patch.object(server, "REQUEST_NOTIFICATION_EMAIL", "owner@example.com"), \
                    patch.object(server, "save_request"), \
                    patch.object(server, "from_json_to_text", return_value="request details"), \
                    patch.object(server, "send_request_notification") as telegram_notification, \
                    patch.object(server, "send_request_email_notification", return_value="sent") as email_notification:
                payload = {
                    "country": country,
                    "selectedCompanies": ["Company A"],
                }

                response = self.client.post("/send_request", json=payload)

                self.assertEqual(response.status_code, 200)
                telegram_notification.assert_called_once_with(
                    "request details",
                    ANY,
                    ["Company A"],
                )
                email_notification.assert_called_once_with(
                    "owner@example.com",
                    "request details",
                    country,
                )

    def test_notification_email_uses_the_same_text_as_telegram(self):
        with patch.object(email_sender, "_deliver_message", return_value="sent") as deliver:
            email_sender.send_request_notification(
                "owner@example.com",
                "the exact Telegram message",
                "usa",
            )

        address, message = deliver.call_args.args
        self.assertEqual(address, "owner@example.com")
        self.assertEqual(
            email_sender._extract_text_body(message),
            "the exact Telegram message",
        )


if __name__ == "__main__":
    unittest.main()
