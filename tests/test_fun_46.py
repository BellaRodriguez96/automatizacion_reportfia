import uuid

from helpers import config
from pages.login_page import LoginPage
from pages.maintenance.funds_page import MaintenanceFundsPage
from pages.navigation import NavigationMenu


def test_fun_46_crear_fondo(manager):
    login_page = manager.get(LoginPage)
    login_page.ensure_logged_in(config.MAINTENANCE_USER, config.MAINTENANCE_PASSWORD)

    navigation = manager.get(NavigationMenu)
    navigation.go_to_maintenance_funds()

    fondos = manager.get(MaintenanceFundsPage)
    assert fondos.table_is_visible(), "El listado de fondos no se cargó correctamente."

    fondos.open_add_modal()
    nombre = f"Fondo QA {uuid.uuid4().hex[:6]}"
    descripcion = "Fondo creado automáticamente desde la prueba FUN-46."
    fondos.fill_form(nombre, descripcion, activo=True)
    fondos.save()

    fondos.filter_by_name(nombre)
    fondos.apply_filters()
    assert fondos.table_contains_fund(nombre), "El nuevo fondo no aparece en el listado después de guardarlo."
