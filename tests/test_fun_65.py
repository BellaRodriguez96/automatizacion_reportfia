from helpers import config
from helpers.data_factory import ensure_test_image, random_description
from pages.login_page import LoginPage
from pages.navigation import NavigationMenu
from pages.reports.list_page import ReportsListPage
from pages.reports.register_page import ReportsRegisterPage


def test_fun_65_registro_reporte(manager):
    login_page = manager.get(LoginPage)
    login_page.ensure_logged_in(config.DEFAULT_USER, config.DEFAULT_PASSWORD)

    nav = manager.get(NavigationMenu)
    nav.go_to_reports_list()

    list_page = manager.get(ReportsListPage)
    list_page.open_register_form()

    register_page = manager.get(ReportsRegisterPage)
    _incident = register_page.select_random_incident()
    descripcion = random_description()
    register_page.set_description(descripcion)
    _lugar = register_page.select_random_location()
    imagen = ensure_test_image()
    register_page.upload_evidence(imagen)

    mensaje = register_page.submit_report()
    assert mensaje or register_page.get_notification(), "No se mostró notificación al enviar el reporte."

    target_list_url = f"{config.BASE_URL}/reportes/listado-general"
    manager.driver.get(target_list_url)
    list_page.wait_for_url_contains("/reportes/listado-general", timeout=30)
    list_page.select_today()
    list_page.apply_filters()

    assert "/reportes/listado-general" in manager.driver.current_url
