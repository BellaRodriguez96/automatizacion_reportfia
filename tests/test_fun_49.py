from helpers import config
from helpers.data_factory import random_resource_name
from pages.login_page import LoginPage
from pages.navigation import NavigationMenu
from pages.maintenance.resources_page import MaintenanceResourcesPage


def test_fun_49_registro_recurso(manager):
    login_page = manager.get(LoginPage)
    login_page.ensure_logged_in(config.MAINTENANCE_USER, config.MAINTENANCE_PASSWORD)

    nav = manager.get(NavigationMenu)
    nav.go_to_maintenance_resources()

    resources_page = manager.get(MaintenanceResourcesPage)
    resources_page.open_add_modal()

    resource_name = random_resource_name()
    resources_page.fill_form(resource_name)
    resources_page.save_resource()

    assert resources_page.get_notification(), "No se mostró notificación al registrar el recurso."

    resources_page.filter_by_name(resource_name)
    resources_page.apply_filters()
    assert resources_page.table_contains_resource(resource_name), "El recurso creado no aparece en la tabla."
