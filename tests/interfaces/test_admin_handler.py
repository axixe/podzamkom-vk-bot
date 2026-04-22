from datetime import datetime
from unittest import TestCase
from unittest.mock import Mock

from domain.models import PhotoQueueItemForReview
from interfaces.admin_handler import AdminHandler
from use_cases.review_queue_item_errors import QueueItemDecisionError


class AdminHandlerTest(TestCase):
    def setUp(self) -> None:
        self.create_employee_use_case = Mock()
        self.list_employees_use_case = Mock()
        self.deactivate_employee_use_case = Mock()
        self.take_next_pending_for_review_use_case = Mock()
        self.approve_queue_item_use_case = Mock()
        self.reject_queue_item_use_case = Mock()

        self.handler = AdminHandler(
            create_employee_use_case=self.create_employee_use_case,
            list_employees_use_case=self.list_employees_use_case,
            deactivate_employee_use_case=self.deactivate_employee_use_case,
            take_next_pending_for_review_use_case=self.take_next_pending_for_review_use_case,
            approve_queue_item_use_case=self.approve_queue_item_use_case,
            reject_queue_item_use_case=self.reject_queue_item_use_case,
        )

    def test_buttons_command_returns_new_simple_actions(self) -> None:
        result = self.handler.handle_text(text="кнопки", from_id=101)

        self.assertEqual(result, "buttons:Следующий|Одобрить|Отклонить|Сотрудники")

    def test_next_returns_queue_item_card(self) -> None:
        self.take_next_pending_for_review_use_case.execute.return_value = PhotoQueueItemForReview(
            id=7,
            employee_id=44,
            photo_url="https://example.com/photo.jpg",
            status="in_review",
            review_started_at=datetime(2026, 1, 5, 10, 20, 30),
            reviewed_at=None,
        )

        result = self.handler.handle_text(text="Следующий", from_id=101)

        self.assertEqual(
            result,
            "queue_item_card:id=7;employee=44;status=in_review;time=2026-01-05 10:20:30",
        )

    def test_approve_uses_selected_queue_item(self) -> None:
        self.take_next_pending_for_review_use_case.execute.return_value = PhotoQueueItemForReview(
            id=12,
            employee_id=44,
            photo_url="https://example.com/photo.jpg",
            status="in_review",
            review_started_at=datetime(2026, 1, 5, 10, 20, 30),
            reviewed_at=None,
        )
        self.approve_queue_item_use_case.execute.return_value = PhotoQueueItemForReview(
            id=12,
            employee_id=44,
            photo_url="https://example.com/photo.jpg",
            status="approved",
            review_started_at=datetime(2026, 1, 5, 10, 20, 30),
            reviewed_at=datetime(2026, 1, 5, 10, 25, 0),
        )

        self.handler.handle_text(text="Следующий", from_id=101)
        result = self.handler.handle_text(text="Одобрить", from_id=101)

        self.approve_queue_item_use_case.execute.assert_called_once_with(
            admin_user_id=101,
            queue_item_id=12,
        )
        self.assertEqual(result, "queue_item_approved:12")

    def test_reject_returns_failed_when_decision_is_invalid(self) -> None:
        self.take_next_pending_for_review_use_case.execute.return_value = PhotoQueueItemForReview(
            id=12,
            employee_id=44,
            photo_url="https://example.com/photo.jpg",
            status="in_review",
            review_started_at=datetime(2026, 1, 5, 10, 20, 30),
            reviewed_at=None,
        )
        self.reject_queue_item_use_case.execute.side_effect = QueueItemDecisionError()

        self.handler.handle_text(text="Следующий", from_id=101)
        result = self.handler.handle_text(text="Отклонить", from_id=101)

        self.assertEqual(result, "queue_item_reject_failed")

    def test_employees_action_lists_staff(self) -> None:
        self.list_employees_use_case.execute.return_value = [object(), object()]

        result = self.handler.handle_text(text="Сотрудники", from_id=101)

        self.assertEqual(result, "employees_count:2")
