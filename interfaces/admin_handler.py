from dataclasses import dataclass

from use_cases.employees import (
    CreateEmployeeUseCase,
    DeactivateEmployeeUseCase,
    ListEmployeesUseCase,
)


@dataclass(slots=True)
class AdminHandler:
    create_employee_use_case: CreateEmployeeUseCase
    list_employees_use_case: ListEmployeesUseCase
    deactivate_employee_use_case: DeactivateEmployeeUseCase

    def handle_text(self, text: str) -> str:
        normalized = text.strip()
        if not normalized:
            return "admin_empty_command"

        lowered = normalized.lower()
        if lowered == "list" or lowered.startswith("/list"):
            employees = self.list_employees_use_case.execute()
            return f"employees_count:{len(employees)}"

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
            return "buttons:create|list|deactivate"

        return "admin_unknown_command"
