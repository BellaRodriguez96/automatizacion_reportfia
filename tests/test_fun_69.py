from helpers import config
from pages.bitacora_page import BitacoraPage
from pages.login_page import LoginPage
from pages.navigation import NavigationMenu

VAL_MODEL_TEXT = "Escuela"
VAL_EVENT_TEXT = "Actualizado"
VAL_START_DATE = "15/09/2025"
VAL_END_DATE = "21/11/2025"


def test_fun_69_bitacora_filtros_exactos(manager):
    login_page = manager.get(LoginPage)
    login_page.ensure_logged_in(config.MAINTENANCE_USER, config.MAINTENANCE_PASSWORD)

    navigation = manager.get(NavigationMenu)
    navigation.go_to_bitacora()

    bitacora = manager.get(BitacoraPage)
    bitacora.wait_until_loaded()

    bitacora.set_model(VAL_MODEL_TEXT)
    bitacora.set_event(VAL_EVENT_TEXT)
    bitacora.set_date_range(VAL_START_DATE, VAL_END_DATE)
    bitacora.set_name("")
    bitacora.apply_filters()

    assert bitacora.table_contains(VAL_MODEL_TEXT), "La bitácora filtrada no contiene registros del modelo Escuela."
    assert bitacora.table_contains(VAL_EVENT_TEXT), "La bitácora filtrada no contiene registros con evento Actualizado."
