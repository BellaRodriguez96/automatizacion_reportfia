from helpers import config
from pages.login_page import LoginPage
from pages.navigation import NavigationMenu
from pages.reports.list_page import ReportsListPage


def test_fun_38_filtrado_reportes(manager):
    login_page = manager.get(LoginPage)
    login_page.ensure_logged_in(config.DEFAULT_USER, config.DEFAULT_PASSWORD)

    nav = manager.get(NavigationMenu)
    nav.go_to_reports_list()

    list_page = manager.get(ReportsListPage)
    list_page.select_last_seven_days()
    list_page.apply_filters()

    list_page.filter_by_incident_text("Problemas con baños")
    list_page.apply_filters()

    list_page.filter_by_state("ASIGNADO")
    list_page.apply_filters()

    assert "/reportes/listado-general" in manager.driver.current_url
