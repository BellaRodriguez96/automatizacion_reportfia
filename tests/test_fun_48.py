from helpers import config
from pages.login_page import LoginPage
from pages.navigation import NavigationMenu
from pages.maintenance.resources_page import MaintenanceResourcesPage


def test_fun_48_listado_recursos_visible(manager):
    login_page = manager.get(LoginPage)
    login_page.ensure_logged_in(config.FUNDS_USER, config.FUNDS_PASSWORD)

    navigation = manager.get(NavigationMenu)
    navigation.go_to_maintenance_resources()

    recursos = manager.get(MaintenanceResourcesPage)
    assert recursos.table_is_visible(), "El catálogo de recursos no se cargó."

