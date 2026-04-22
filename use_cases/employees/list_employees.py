from dataclasses import dataclass

from domain.models import Employee
from domain.repositories import EmployeeRepository


@dataclass(slots=True)
class ListEmployeesUseCase:
    employee_repository: EmployeeRepository

    def execute(self) -> list[Employee]:
        return self.employee_repository.list_all()
