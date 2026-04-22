from dataclasses import dataclass, field
from datetime import datetime

from domain.models import PhotoQueueItemForReview
from use_cases.employees import (
    CreateEmployeeUseCase,
    DeactivateEmployeeUseCase,
    ListEmployeesUseCase,
)
from use_cases.approve_queue_item import ApproveQueueItemUseCase
from use_cases.reject_queue_item import RejectQueueItemUseCase
from use_cases.review_queue_item_errors import QueueItemDecisionError
from use_cases.take_next_pending_for_review import TakeNextPendingForReviewUseCase


@dataclass(slots=True)
class AdminHandler:
    create_employee_use_case: CreateEmployeeUseCase
    list_employees_use_case: ListEmployeesUseCase
    deactivate_employee_use_case: DeactivateEmployeeUseCase
    take_next_pending_for_review_use_case: TakeNextPendingForReviewUseCase
    approve_queue_item_use_case: ApproveQueueItemUseCase
    reject_queue_item_use_case: RejectQueueItemUseCase
    _current_item_by_admin: dict[int, int] = field(default_factory=dict)

    def handle_text(self, text: str, from_id: int) -> str:
        normalized = text.strip()
        if not normalized:
            return "admin_empty_command"

        lowered = normalized.lower()
        if lowered == "list" or lowered.startswith("/list"):
            employees = self.list_employees_use_case.execute()
            return f"employees_count:{len(employees)}"

        if lowered in {"сотрудники", "employees", "/employees"}:
            employees = self.list_employees_use_case.execute()
            return f"employees_count:{len(employees)}"

        if lowered in {"следующий", "next", "/next"}:
            item = self.take_next_pending_for_review_use_case.execute(admin_user_id=from_id)
            if item is None:
                self._current_item_by_admin.pop(from_id, None)
                return "queue_empty"

            self._current_item_by_admin[from_id] = item.id
            return self._format_queue_item_card(item)

        if lowered in {"одобрить", "approve", "/approve"}:
            queue_item_id = self._current_item_by_admin.get(from_id)
            if queue_item_id is None:
                return "queue_item_not_selected"
            try:
                item = self.approve_queue_item_use_case.execute(
                    admin_user_id=from_id,
                    queue_item_id=queue_item_id,
                )
            except QueueItemDecisionError:
                return "queue_item_approve_failed"
            return f"queue_item_approved:{item.id}"

        if lowered in {"отклонить", "reject", "/reject"}:
            queue_item_id = self._current_item_by_admin.get(from_id)
            if queue_item_id is None:
                return "queue_item_not_selected"
            try:
                item = self.reject_queue_item_use_case.execute(
                    admin_user_id=from_id,
                    queue_item_id=queue_item_id,
                )
            except QueueItemDecisionError:
                return "queue_item_reject_failed"
            return f"queue_item_rejected:{item.id}"

        if lowered.startswith("create") or lowered.startswith("/create"):
            parts = normalized.split()
            if len(parts) < 2:
                return "create_usage:/create <username> [platform_user_id]"

            username = parts[1]
            try:
                platform_user_id = int(parts[2]) if len(parts) > 2 else None
            except ValueError:
                return "create_usage:/create <username> [platform_user_id]"
            employee = self.create_employee_use_case.execute(
                username=username,
                platform_user_id=platform_user_id,
            )
            return f"employee_created:{employee.id}"

        if lowered.startswith("deactivate") or lowered.startswith("/deactivate"):
            parts = normalized.split()
            if len(parts) < 2:
                return "deactivate_usage:/deactivate <employee_id>"

            try:
                employee_id = int(parts[1])
            except ValueError:
                return "deactivate_usage:/deactivate <employee_id>"
            employee = self.deactivate_employee_use_case.execute(employee_id=employee_id)
            if employee is None:
                return "employee_not_found"

            return f"employee_deactivated:{employee.id}"

        if lowered in {"buttons", "кнопки"}:
            return "buttons:Следующий|Одобрить|Отклонить|Сотрудники"

        return "admin_unknown_command"

    def _format_queue_item_card(self, item: PhotoQueueItemForReview) -> str:
        event_time = item.review_started_at or item.reviewed_at
        event_time_str = self._format_timestamp(event_time)
        return (
            "queue_item_card:"
            f"id={item.id};"
            f"employee={item.employee_id};"
            f"status={item.status};"
            f"time={event_time_str}"
        )

    @staticmethod
    def _format_timestamp(value: datetime | None) -> str:
        if value is None:
            return "-"
        return value.replace(microsecond=0).isoformat(sep=" ")
