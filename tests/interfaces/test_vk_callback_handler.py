import unittest
from unittest.mock import Mock

from interfaces.vk_callback_handler import VkCallbackHandler


class VkCallbackHandlerTest(unittest.TestCase):
    def setUp(self) -> None:
        self.process_vk_callback_use_case = Mock()
        self.process_vk_callback_use_case.execute.return_value = "ok"
        self.admin_handler = Mock()
        self.outgoing_message_service = Mock()
        self.handler = VkCallbackHandler(
            process_vk_callback_use_case=self.process_vk_callback_use_case,
            confirmation_code="confirm-code",
            callback_secret="super-secret",
            admin_user_ids=(101,),
            admin_handler=self.admin_handler,
            outgoing_message_service=self.outgoing_message_service,
        )

    def test_rejects_event_with_invalid_secret_without_use_case_call(self) -> None:
        with self.assertLogs("podzamkom_vk_bot", level="WARNING") as logs:
            result = self.handler.handle({"type": "message_new", "secret": "wrong"})

        self.assertEqual(result, "ok")
        self.process_vk_callback_use_case.execute.assert_not_called()
        self.assertIn("error=secret mismatch", logs.output[0])
        self.assertIn("correlation_id=<missing-event-id>", logs.output[0])
        self.assertNotIn("wrong", logs.output[0])

    def test_rejects_event_with_missing_type_without_use_case_call(self) -> None:
        with self.assertLogs("podzamkom_vk_bot", level="WARNING") as logs:
            result = self.handler.handle({"secret": "super-secret"})

        self.assertEqual(result, "ok")
        self.process_vk_callback_use_case.execute.assert_not_called()
        self.assertIn("error=missing event type", logs.output[0])
        self.assertIn("correlation_id=<missing-event-id>", logs.output[0])

    def test_rejects_message_event_with_missing_event_id(self) -> None:
        with self.assertLogs("podzamkom_vk_bot", level="WARNING") as logs:
            result = self.handler.handle(
                {
                    "type": "message_new",
                    "secret": "super-secret",
                    "object": {"message": {"from_id": 101, "attachments": []}},
                }
            )

        self.assertEqual(result, "ok")
        self.process_vk_callback_use_case.execute.assert_not_called()
        self.assertIn("error=missing event_id", logs.output[0])
        self.assertIn("correlation_id=<missing-event-id>", logs.output[0])

    def test_returns_confirmation_code_with_use_case_call(self) -> None:
        self.process_vk_callback_use_case.execute.return_value = "need_confirmation_code"
        result = self.handler.handle({"type": "confirmation", "secret": "super-secret"})

        self.assertEqual(result, "confirm-code")
        self.process_vk_callback_use_case.execute.assert_called_once_with(
            event_type="confirmation",
            payload={"type": "confirmation", "secret": "super-secret"},
        )

    def test_rejects_confirmation_with_invalid_secret_without_use_case_call(self) -> None:
        with self.assertLogs("podzamkom_vk_bot", level="WARNING") as logs:
            result = self.handler.handle({"type": "confirmation", "secret": "bad"})

        self.assertEqual(result, "ok")
        self.process_vk_callback_use_case.execute.assert_not_called()
        self.assertIn("error=secret mismatch for confirmation event", logs.output[0])
        self.assertNotIn("bad", logs.output[0])

    def test_ignores_unsupported_event_type_as_no_op(self) -> None:
        with self.assertLogs("podzamkom_vk_bot", level="INFO") as logs:
            result = self.handler.handle(
                {
                    "type": "photo_new",
                    "secret": "super-secret",
                    "event_id": "evt-unsupported-1",
                }
            )

        self.assertEqual(result, "ok")
        self.process_vk_callback_use_case.execute.assert_not_called()
        self.assertIn("Ignoring unsupported event type", logs.output[-1])

    def test_skips_admin_side_effects_for_duplicate_message_event(self) -> None:
        self.process_vk_callback_use_case.execute.return_value = "duplicate_event"

        result = self.handler.handle(
            {
                "type": "message_new",
                "secret": "super-secret",
                "event_id": "evt-1",
                "object": {"message": {"from_id": 101, "text": "/next", "payload": {}}},
            }
        )

        self.assertEqual(result, "ok")
        self.admin_handler.handle_text.assert_not_called()

    def test_runs_admin_handler_for_non_duplicate_message_event(self) -> None:
        self.process_vk_callback_use_case.execute.return_value = "ok"
        self.admin_handler.handle_text.return_value = "queue_empty"

        result = self.handler.handle(
            {
                "type": "message_new",
                "secret": "super-secret",
                "event_id": "evt-2",
                "object": {"message": {"from_id": 101, "text": "/next", "payload": {}}},
            }
        )

        self.assertEqual(result, "ok")
        self.admin_handler.handle_text.assert_called_once_with(text="/next", from_id=101)

    def test_returns_main_menu_for_start_command(self) -> None:
        self.process_vk_callback_use_case.execute.return_value = "show_main_menu"

        result = self.handler.handle(
            {
                "type": "message_new",
                "secret": "super-secret",
                "event_id": "evt-menu-1",
                "object": {"message": {"from_id": 101, "text": "Начать"}},
            }
        )

        self.assertEqual(result, "ok")
        self.outgoing_message_service.send_message.assert_called_once()
        _, kwargs = self.outgoing_message_service.send_message.call_args
        self.assertIn("Employee", kwargs["text"])
        self.assertIn("Admin", kwargs["text"])
        self.assertIn("Guest", kwargs["text"])
        self.assertIn("🏠 Главное меню", kwargs["text"])
        self.assertEqual(kwargs["user_id"], 101)
        self.assertIsInstance(kwargs["keyboard"], str)

    def test_adds_main_menu_to_completed_action_response(self) -> None:
        self.process_vk_callback_use_case.execute.return_value = "draft_cleared:2"

        result = self.handler.handle(
            {
                "type": "message_new",
                "secret": "super-secret",
                "event_id": "evt-menu-2",
                "object": {"message": {"from_id": 101, "text": "/clear"}},
            }
        )

        self.assertEqual(result, "ok")
        self.outgoing_message_service.send_message.assert_called_once()
        _, kwargs = self.outgoing_message_service.send_message.call_args
        self.assertIn("Черновик очищен", kwargs["text"])
        self.assertIn("🏠 Главное меню", kwargs["text"])

    def test_allows_text_only_message_for_message_new_validation(self) -> None:
        result = self.handler.handle(
            {
                "type": "message_new",
                "secret": "super-secret",
                "event_id": "evt-menu-3",
                "object": {"message": {"from_id": 101, "text": "Начать"}},
            }
        )

        self.assertEqual(result, "ok")
        self.process_vk_callback_use_case.execute.assert_called_once()

    def test_sends_reply_to_vk_for_role_selected_result(self) -> None:
        self.process_vk_callback_use_case.execute.return_value = "role_selected:guest"

        result = self.handler.handle(
            {
                "type": "message_new",
                "secret": "super-secret",
                "event_id": "evt-role-1",
                "object": {"message": {"from_id": 101, "text": "Guest"}},
            }
        )

        self.assertEqual(result, "ok")
        self.outgoing_message_service.send_message.assert_called_once()

    def test_retries_without_keyboard_when_first_send_fails(self) -> None:
        self.process_vk_callback_use_case.execute.return_value = "show_main_menu"
        self.outgoing_message_service.send_message.side_effect = [RuntimeError("vk error"), None]

        result = self.handler.handle(
            {
                "type": "message_new",
                "secret": "super-secret",
                "event_id": "evt-retry-1",
                "object": {"message": {"from_id": 101, "text": "Начать"}},
            }
        )

        self.assertEqual(result, "ok")
        self.assertEqual(self.outgoing_message_service.send_message.call_count, 2)
        first_call = self.outgoing_message_service.send_message.call_args_list[0].kwargs
        second_call = self.outgoing_message_service.send_message.call_args_list[1].kwargs
        self.assertIsInstance(first_call["keyboard"], str)
        self.assertIsNone(second_call["keyboard"])


if __name__ == "__main__":
    unittest.main()
