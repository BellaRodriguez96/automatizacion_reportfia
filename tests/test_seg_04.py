import pytest

from pages.login_page import LoginPage

INVALID_USER = "usuario.noexiste@ues.edu.sv"
INVALID_PASSWORD = "ClaveInvalida123"


@pytest.mark.no_profile
def test_seg_04_login_usuario_inexistente(manager):
    login_page = manager.get(LoginPage)
    base = manager.base

    login_page.go_to_login()
    assert not base.detect_http_500(), "Error 500 al cargar la pantalla de login."

    login_page.login(INVALID_USER, INVALID_PASSWORD)
    assert login_page.is_on_login_page(), "El sistema permitió continuar con credenciales inexistentes."

    error = login_page.get_error_notification()
    assert error, "No se mostró mensaje de error para el usuario inexistente."
