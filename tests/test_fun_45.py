import pytest

from helpers import config
from pages.login_page import LoginPage
from pages.navigation import NavigationMenu
from pages.maintenance.funds_page import MaintenanceFundsPage


@pytest.mark.clean_profile
def test_fun_45_listado_fondos_se_muestra(manager):
    login_page = manager.get(LoginPage)
    login_page.ensure_logged_in(config.FUNDS_USER, config.FUNDS_PASSWORD)

    navigation = manager.get(NavigationMenu)
    navigation.go_to_maintenance_funds()

    fondos = manager.get(MaintenanceFundsPage)
    assert fondos.table_is_visible(), "La tabla de fondos no se cargó correctamente."
