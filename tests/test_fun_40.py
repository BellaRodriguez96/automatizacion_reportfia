import time

from helpers import config
from pages.login_page import LoginPage
from pages.navigation import NavigationMenu
from pages.reports.detail_page import ReportDetailPage
from pages.reports.list_page import ReportsListPage


def test_fun_40_consultar_detalle_reporte(manager):
    login_page = manager.get(LoginPage)
    login_page.ensure_logged_in(config.MAINTENANCE_USER, config.MAINTENANCE_PASSWORD)

    navigation = manager.get(NavigationMenu)
    navigation.go_to_reports_list()

    listado = manager.get(ReportsListPage)
    listado.wait_until_ready()
    detail_url = listado.open_first_detail()

    time.sleep(2)

    detalle = manager.get(ReportDetailPage)
    detalle.wait_until_loaded()

    assert "/reportes/detalle" in manager.driver.current_url, "No se abrió la página de detalle."
    assert not manager.base.detect_http_500(), "El detalle mostró un error 500."

    assert detalle.has_general_information(), "No se muestra la información general del reporte."
    assert detalle.has_state_information(), "No se visualiza el estado del reporte."
    assert detalle.has_assignment_information(), "No se muestra la información de asignación/responsable."
    assert detalle.has_history_information(), "No se muestra la sección de historial."
    assert detalle.has_evidence_section(), "No se encontró información de evidencias."

    time.sleep(5)
