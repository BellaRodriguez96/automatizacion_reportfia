from helpers import config
from helpers.data_factory import ensure_test_image, random_description
from pages.login_page import LoginPage
from pages.navigation import NavigationMenu
from pages.reports.list_page import ReportsListPage
from pages.reports.register_page import ReportsRegisterPage


def test_fun_39_registro_reporte(manager):
    login_page = manager.get(LoginPage)
    login_page.ensure_logged_in(config.MAINTENANCE_USER, config.MAINTENANCE_PASSWORD)

    navigation = manager.get(NavigationMenu)
    navigation.go_to_reports_list()

    listado = manager.get(ReportsListPage)
    listado.open_register_form()

    registro = manager.get(ReportsRegisterPage)
    registro.select_incident_by_text("Problemas con baños")
    registro.set_description(random_description())
    registro.select_location_by_text("C11")
    evidencia = ensure_test_image()
    registro.upload_evidence(evidencia)

    mensaje = registro.submit_report()
    assert "/reportes" in manager.driver.current_url, "No se redirigió a la vista de reportes después de enviar."
    assert "reporte" in mensaje.lower() or registro.get_notification(), "No se mostró confirmación del registro."
