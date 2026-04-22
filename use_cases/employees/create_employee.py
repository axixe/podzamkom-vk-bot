from dataclasses import dataclass

from domain.models import Employee
from domain.repositories import EmployeeRepository


@dataclass(slots=True)
class CreateEmployeeUseCase:
    employee_repository: EmployeeRepository

    def execute(self, username: str, platform_user_id: int | None = None) -> Employee:
        normalized_username = username.strip()
        if not normalized_username:
            raise ValueError("username must not be empty")

        return self.employee_repository.create(
            username=normalized_username,
            platform_user_id=platform_user_id,
        )
