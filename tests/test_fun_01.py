import pytest

from helpers import config
from pages.login_page import LoginPage
from pages.two_factor_page import TwoFactorPage


def test_fun_01_login_con_2fa(manager):
    login_page = manager.get(LoginPage)
    login_page.go_to_login()
    login_page.login(config.MAINTENANCE_USER, config.MAINTENANCE_PASSWORD)

    state, message = login_page.wait_for_auth_state()
    if state == "error":
        pytest.fail(f"Error durante el login: {message}")

    if state == "two_factor":
        two_factor_page = manager.get(TwoFactorPage)
        two_factor_page.complete_two_factor_flow(config.MAINTENANCE_USER)
        login_page.wait_for_url_contains("/inicio")
    elif state != "home":
        pytest.fail(f"Estado inesperado después del login: {state}")

    assert login_page.is_logged_in(), "No se llegó a la página de inicio después del login."
    login_page.remember_login_success(config.MAINTENANCE_USER, config.MAINTENANCE_PASSWORD)
