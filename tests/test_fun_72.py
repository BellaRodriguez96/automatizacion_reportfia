import pytest

from pages.login_page import LoginPage


@pytest.mark.clean_profile
@pytest.mark.no_profile
def test_fun_72_login_campos_vacios(manager):
    login_page = manager.get(LoginPage)
    login_page.go_to_login()

    login_page.login("", "")
    error = login_page.get_error_notification()

    assert login_page.is_on_login_page(), "El sistema permitió iniciar sesión con campos vacíos."
    assert error or not login_page.is_logged_in(), "No se mostró mensaje de error ante credenciales vacías."
