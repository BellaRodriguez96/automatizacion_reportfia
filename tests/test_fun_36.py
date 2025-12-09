from helpers import config
from helpers.data_factory import random_school_name
from pages.login_page import LoginPage
from pages.navigation import NavigationMenu
from pages.maintenance.schools_page import MaintenanceSchoolsPage


def test_fun_36_registro_escuela(manager):
    login_page = manager.get(LoginPage)
    login_page.ensure_logged_in(config.MAINTENANCE_USER, config.MAINTENANCE_PASSWORD)

    nav = manager.get(NavigationMenu)
    nav.go_to_maintenance_schools()

    schools_page = manager.get(MaintenanceSchoolsPage)
    schools_page.open_add_modal()
    school_name = random_school_name()
    schools_page.fill_form(school_name)
    schools_page.save_school()

    assert schools_page.get_notification(), "No apareció notificación al crear la escuela."

    schools_page.filter_by_name(school_name)
    schools_page.apply_filters()
    assert schools_page.table_contains_school(school_name), "La escuela creada no aparece luego de filtrar."
