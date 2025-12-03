from helpers import config
from pages.login_page import LoginPage
from pages.navigation import NavigationMenu
from pages.maintenance.assets_page import MaintenanceAssetsPage

NOMBRE_EJEMPLO = "SILLA RECLINABLE V2"
CODIGO_EJEMPLO = "S-6011"
ESTADO_VALUE = "1"
ESTADO_TEXTO = "ACTIVO"


def test_fun_59_filtros_bienes(manager):
    login_page = manager.get(LoginPage)
    login_page.ensure_logged_in(config.MAINTENANCE_USER, config.MAINTENANCE_PASSWORD)

    navigation = manager.get(NavigationMenu)
    navigation.go_to_maintenance_assets()

    bienes = manager.get(MaintenanceAssetsPage)
    bienes.wait_until_ready()

    bienes.filter_by_name(NOMBRE_EJEMPLO)
    bienes.apply_filters()
    assert bienes.table_contains_text(NOMBRE_EJEMPLO), "El filtro por nombre no arrojó resultados."

    bienes.reset_filters()
    bienes.filter_by_code(CODIGO_EJEMPLO)
    bienes.apply_filters()
    assert bienes.table_contains_text(CODIGO_EJEMPLO), "El filtro por código no devolvió registros."

    bienes.reset_filters()
    bienes.filter_by_status(ESTADO_VALUE)
    bienes.apply_filters()
    assert bienes.table_contains_text(ESTADO_TEXTO), "El filtro por estado no mostró registros activos."
