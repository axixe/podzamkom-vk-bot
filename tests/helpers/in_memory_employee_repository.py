from datetime import datetime, timezone

from domain.models import Employee


class InMemoryEmployeeRepository:
    def __init__(self, employees: list[Employee] | None = None) -> None:
        self._employees = {employee.id: employee for employee in (employees or [])}
        self._next_id = max(self._employees.keys(), default=0) + 1

    def create(self, username: str, platform_user_id: int | None = None) -> Employee:
        now = datetime.now(timezone.utc)
        employee = Employee(
            id=self._next_id,
            username=username,
            platform_user_id=platform_user_id,
            is_active=True,
            created_at=now,
            updated_at=now,
        )
        self._employees[employee.id] = employee
        self._next_id += 1
        return employee

    def list_all(self) -> list[Employee]:
        return [self._employees[key] for key in sorted(self._employees)]

    def deactivate(self, employee_id: int) -> Employee | None:
        employee = self._employees.get(employee_id)
        if employee is None:
            return None

        updated = Employee(
            id=employee.id,
            username=employee.username,
            platform_user_id=employee.platform_user_id,
            is_active=False,
            created_at=employee.created_at,
            updated_at=datetime.now(timezone.utc),
        )
        self._employees[employee_id] = updated
        return updated

    def find_active_by_platform_user_id(self, platform_user_id: int) -> Employee | None:
        for employee in self._employees.values():
            if employee.platform_user_id == platform_user_id and employee.is_active:
                return employee

        return None
