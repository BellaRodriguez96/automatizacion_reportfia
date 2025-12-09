import pytest

from helpers import config
from pages.hr.assign_position_modal import AssignPositionModal
from pages.hr.employees_page import EmployeesPage
from pages.login_page import LoginPage
from pages.navigation import NavigationMenu


def test_fun_27_asignacion_puesto_empleado(manager):
    login_page = manager.get(LoginPage)
    login_page.logout_and_clear()

    login_page.ensure_logged_in(
        config.MAINTENANCE_USER,
        config.MAINTENANCE_PASSWORD,
        auto_two_factor=True,
    )
    assert login_page.is_logged_in(), "El usuario aa11001 no pudo acceder al dashboard de ReportFIA."
    assert not login_page.requires_two_factor(), "El flujo quedo detenido en Two Factor despues del login."

    navigation = manager.get(NavigationMenu)
    navigation.go_to_hr_employees()

    employees_page = manager.get(EmployeesPage)
    employees_page.wait_until_ready()
    assert employees_page.has_existing_assignments(), "No fue posible visualizar las asignaciones actuales del empleado."

    candidate_pool = list(config.FUN27_EMPLOYEE_CANDIDATES) or [None]
    conflict_message = "el empleado ya tiene asignado el puesto seleccionado"
    assignment_confirmed = False
    assignment_data = None
    success_text = ""

    for candidate in candidate_pool:
        entity_exclusions: set[str] = set()
        employee_offset = 0
        for attempt in range(6):
            employees_page.open_assign_position_modal()
            modal = manager.get(AssignPositionModal)
            modal.wait_until_ready()

            assignment_data = modal.fill_assignment_form(
                employee_name=candidate,
                entity_name=config.FUN27_ENTITY_NAME,
                position_name=config.FUN27_POSITION_NAME,
                status_label=config.FUN27_STATUS_LABEL,
                exclude_entities=entity_exclusions,
                employee_index_offset=employee_offset,
            )
            employee_offset += 1

            success_text = modal.submit()
            normalized_message = (success_text or "").strip().lower()
            if success_text == config.FUN27_SUCCESS_MESSAGE:
                assignment_confirmed = True
                break
            if conflict_message in normalized_message:
                continue
            entity_exclusions.add(assignment_data["entity"])
            pytest.fail(f"El sistema respondio con un mensaje inesperado: {success_text!r}")

        if success_text == config.FUN27_SUCCESS_MESSAGE:
            break

    if success_text != config.FUN27_SUCCESS_MESSAGE or not assignment_confirmed:
        pytest.fail(f"No se pudo asignar un puesto valido. Mensaje recibido: {success_text or 'sin mensaje'}")

    assert not login_page.requires_two_factor(), "El sistema intento redirigir a Two Factor despues del guardado."
    assert not manager.base.detect_http_500(), "Se detecto una pagina de error 500 durante el flujo de asignacion."
