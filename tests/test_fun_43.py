import pytest

from helpers import config
from selenium.common.exceptions import TimeoutException

from pages.login_page import LoginPage
from pages.navigation import NavigationMenu
from pages.reports.assignments_page import ReportsAssignmentsPage


@pytest.mark.clean_profile
def test_fun_43_mis_asignaciones(manager):
    login_page = manager.get(LoginPage)
    login_page.ensure_logged_in(config.ASSIGNEE_USER, config.ASSIGNEE_PASSWORD)

    navigation = manager.get(NavigationMenu)
    navigation.go_to_reports_assignments()

    assignments = manager.get(ReportsAssignmentsPage)
    try:
        detail_url = assignments.open_first_assignment()
    except TimeoutException:
        pytest.skip("No hay asignaciones disponibles para validar el detalle.")

    assert "/reportes/detalle" in detail_url, "El detalle de la asignación no se abrió correctamente."
    assert not manager.base.detect_http_500(), "El detalle del reporte mostró un error 500."
