import unittest
from unittest.mock import Mock

from interfaces.vk_callback_handler import VkCallbackHandler


class VkCallbackHandlerTest(unittest.TestCase):
    def setUp(self) -> None:
        self.process_vk_callback_use_case = Mock()
        self.process_vk_callback_use_case.execute.return_value = "ok"
        self.admin_handler = Mock()
        self.handler = VkCallbackHandler(
            process_vk_callback_use_case=self.process_vk_callback_use_case,
            confirmation_code="confirm-code",
            callback_secret="super-secret",
            admin_user_ids=(101,),
            admin_handler=self.admin_handler,
        )

    def test_rejects_event_with_invalid_secret_without_use_case_call(self) -> None:
        with self.assertLogs("podzamkom_vk_bot", level="WARNING") as logs:
            result = self.handler.handle({"type": "message_new", "secret": "wrong"})

        self.assertEqual(result, "ok")
        self.process_vk_callback_use_case.execute.assert_not_called()
        self.assertIn("Callback rejected: secret mismatch", logs.output[0])
        self.assertNotIn("wrong", logs.output[0])

    def test_rejects_event_with_missing_type_without_use_case_call(self) -> None:
        with self.assertLogs("podzamkom_vk_bot", level="WARNING") as logs:
            result = self.handler.handle({"secret": "super-secret"})

        self.assertEqual(result, "ok")
        self.process_vk_callback_use_case.execute.assert_not_called()
        self.assertIn("Callback rejected: missing event type", logs.output[0])

    def test_returns_confirmation_code_without_use_case_call(self) -> None:
        result = self.handler.handle({"type": "confirmation", "secret": "super-secret"})

        self.assertEqual(result, "confirm-code")
        self.process_vk_callback_use_case.execute.assert_not_called()

    def test_rejects_confirmation_with_invalid_secret_without_use_case_call(self) -> None:
        with self.assertLogs("podzamkom_vk_bot", level="WARNING") as logs:
            result = self.handler.handle({"type": "confirmation", "secret": "bad"})

        self.assertEqual(result, "ok")
        self.process_vk_callback_use_case.execute.assert_not_called()
        self.assertIn("Callback rejected: secret mismatch for confirmation event", logs.output[0])
        self.assertNotIn("bad", logs.output[0])


if __name__ == "__main__":
    unittest.main()
