from helpers import config
from helpers.data_factory import student_data
from pages.login_page import LoginPage
from pages.navigation import NavigationMenu
from pages.security.users_page import SecurityUsersPage


def test_fun_15_crear_usuario_empleado(manager):
    login_page = manager.get(LoginPage)
    login_page.ensure_logged_in(config.MAINTENANCE_USER, config.MAINTENANCE_PASSWORD)

    navigation = manager.get(NavigationMenu)
    navigation.go_to_security_users()

    users_page = manager.get(SecurityUsersPage)
    users_page.open_add_modal()
    data = student_data()
    users_page.fill_user_form(data)
    users_page.save_user()
    assert users_page.get_notification(), "No se mostró confirmación al crear el usuario empleado."

    users_page.filter_by_email(data.email)
    users_page.apply_filters()
    assert users_page.table_contains_email(data.email), "El usuario creado no aparece luego de filtrar por correo."
