import time
import uuid

from helpers import config
from pages.login_page import LoginPage
from pages.navigation import NavigationMenu
from pages.reports.assignment_form import ReportAssignmentForm
from pages.reports.list_page import ReportsListPage
from pages.reports.detail_page import ReportDetailPage


def test_fun_41_asignar_recursos_y_responsables(manager):
    login_page = manager.get(LoginPage)
    login_page.ensure_logged_in(config.MAINTENANCE_USER, config.MAINTENANCE_PASSWORD)

    navigation = manager.get(NavigationMenu)
    navigation.go_to_reports_list()
    listado = manager.get(ReportsListPage)
    listado.wait_until_ready()
    listado.open_first_detail()

    time.sleep(2)

    detalle = manager.get(ReportDetailPage)
    detalle.wait_until_loaded()

    formulario = manager.get(ReportAssignmentForm)
    formulario.reset_form()
    formulario.select_entity("DECANATO")
    formulario.add_employee("RODRIGO PALMERA")
    formulario.add_supervisor("MISAEL GOMEZ")
    formulario.add_first_resource()
    formulario.select_category("Baja (Simple) - (1 horas)")
    comentario = f"Asignacion automatica QA {uuid.uuid4().hex[:6]}"
    formulario.set_comment(comentario)
    mensaje = formulario.submit()
    time.sleep(3)

    assert mensaje, "No se mostro confirmacion al asignar el reporte."

    detalle.wait_until_loaded()
    assert detalle.page_contains("RODRIGO PALMERA"), "El detalle no refleja al responsable asignado."
    assert detalle.page_contains("DECANATO"), "El detalle no muestra la entidad asignada."

    time.sleep(5)
