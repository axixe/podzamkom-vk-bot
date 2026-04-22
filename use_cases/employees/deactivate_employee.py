from dataclasses import dataclass

from domain.models import Employee
from domain.repositories import EmployeeRepository


@dataclass(slots=True)
class DeactivateEmployeeUseCase:
    employee_repository: EmployeeRepository

    def execute(self, employee_id: int) -> Employee | None:
        return self.employee_repository.deactivate(employee_id=employee_id)
