import unittest

from tests.helpers.in_memory_employee_repository import InMemoryEmployeeRepository
from use_cases.employees import (
    CreateEmployeeUseCase,
    DeactivateEmployeeUseCase,
    ListEmployeesUseCase,
)


class EmployeeUseCasesTest(unittest.TestCase):
    def test_create_and_list(self) -> None:
        repository = InMemoryEmployeeRepository()
        create_use_case = CreateEmployeeUseCase(employee_repository=repository)
        list_use_case = ListEmployeesUseCase(employee_repository=repository)

        create_use_case.execute(username="alice", platform_user_id=101)

        employees = list_use_case.execute()
        self.assertEqual(len(employees), 1)
        self.assertEqual(employees[0].username, "alice")
        self.assertTrue(employees[0].is_active)

    def test_deactivate_employee(self) -> None:
        repository = InMemoryEmployeeRepository()
        employee = repository.create(username="bob", platform_user_id=202)
        deactivate_use_case = DeactivateEmployeeUseCase(employee_repository=repository)

        updated = deactivate_use_case.execute(employee_id=employee.id)

        self.assertIsNotNone(updated)
        assert updated is not None
        self.assertFalse(updated.is_active)


if __name__ == "__main__":
    unittest.main()
