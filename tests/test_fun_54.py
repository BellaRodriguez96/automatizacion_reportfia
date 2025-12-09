import uuid

from helpers import config
from pages.login_page import LoginPage
from pages.maintenance.units_page import MaintenanceUnitsPage
from pages.navigation import NavigationMenu


def test_fun_54_crear_unidad_medida(manager):
    login_page = manager.get(LoginPage)
    login_page.ensure_logged_in(config.MAINTENANCE_USER, config.MAINTENANCE_PASSWORD)

    navigation = manager.get(NavigationMenu)
    navigation.go_to_maintenance_units()

    unidades = manager.get(MaintenanceUnitsPage)
    assert unidades.table_is_visible(), "No se cargó el listado de unidades de medida."

    unidades.open_add_modal()
    nombre = f"Unidad QA {uuid.uuid4().hex[:4]}"
    unidades.fill_form(nombre, activo=True)
    unidades.save()

    unidades.filter_by_name(nombre)
    unidades.apply_filters()

    assert unidades.table_contains_unit(nombre), "La unidad creada no aparece en la tabla."
