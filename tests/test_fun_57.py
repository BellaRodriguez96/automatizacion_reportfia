import time

from helpers import config
from pages.login_page import LoginPage
from pages.navigation import NavigationMenu
from pages.maintenance.incident_types_page import IncidentTypesPage


def test_fun_57_crear_tipo_incidencia(manager):
    login_page = manager.get(LoginPage)
    login_page.ensure_logged_in(config.MAINTENANCE_USER, config.MAINTENANCE_PASSWORD)

    navigation = manager.get(NavigationMenu)
    navigation.go_to_maintenance_incident_types()

    incident_types = manager.get(IncidentTypesPage)
    incident_types.open_add_modal()

    nombre = f"Tipo prueba {int(time.time())}"
    descripcion = "Descripción generada automáticamente por la suite FUN-57."

    incident_types.fill_form(nombre, descripcion, active=True)
    incident_types.submit()
    incident_types.filter_by_name(nombre)

    assert incident_types.table_contains(nombre), "El nuevo tipo de incidencia no aparece en el listado."
