from helpers import config
from helpers.data_factory import student_data
from pages.login_page import LoginPage
from pages.navigation import NavigationMenu
from pages.security.users_page import SecurityUsersPage


def test_fun_75_registro_usuario_correo_existente(manager):
    login_page = manager.get(LoginPage)
    login_page.ensure_logged_in(config.DEFAULT_USER, config.DEFAULT_PASSWORD)

    nav = manager.get(NavigationMenu)
    nav.go_to_security_users()

    users_page = manager.get(SecurityUsersPage)
    users_page.open_add_modal()

    data = student_data(carnet=config.DEFAULT_USER.upper())
    users_page.fill_user_form(data)
    users_page.save_user()

    notification = users_page.get_notification()
    assert notification, "No se recibió notificación al intentar registrar un correo ya existente."
