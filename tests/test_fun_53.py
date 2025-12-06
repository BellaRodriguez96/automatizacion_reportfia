from helpers import config
from pages.login_page import LoginPage
from pages.navigation import NavigationMenu
from pages.maintenance.units_page import MaintenanceUnitsPage


def test_fun_53_listado_unidades_medida(manager):
    login_page = manager.get(LoginPage)
    login_page.ensure_logged_in(config.MAINTENANCE_USER, config.MAINTENANCE_PASSWORD)

    navigation = manager.get(NavigationMenu)
    navigation.go_to_maintenance_units()

    unidades = manager.get(MaintenanceUnitsPage)
    unidades.wait_until_list_ready()

    assert not manager.base.detect_http_500(), "El listado de unidades mostró un error 500."
    assert unidades.has_required_headers(
        ["nombre", "estado"]
    ), "Las columnas esperadas no se visualizaron en el listado."
    assert unidades.has_data_rows(), "El listado de unidades apareció vacío inesperadamente."
    assert unidades.first_row_has_values(), "Los registros mostrados no contienen información válida."
