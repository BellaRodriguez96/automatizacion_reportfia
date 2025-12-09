from helpers import config
from pages.login_page import LoginPage
from pages.navigation import NavigationMenu
from pages.maintenance.incident_types_page import IncidentTypesPage


def test_fun_56_tipologias_listado_visible(manager):
    login_page = manager.get(LoginPage)
    login_page.ensure_logged_in(config.MAINTENANCE_USER, config.MAINTENANCE_PASSWORD)

    navigation = manager.get(NavigationMenu)
    navigation.go_to_maintenance_incident_types()

    incident_types = manager.get(IncidentTypesPage)
    assert incident_types.is_loaded(), "El listado de tipos de incidencia no se cargó."
