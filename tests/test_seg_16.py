import pytest

from helpers import config
from pages.login_page import LoginPage

PASSWORDS_INVALIDAS = ["admin123", "1234", "", "     ", "password", "letmein", "qwerty", "12345678"]


@pytest.mark.clean_profile
def test_seg_16_passwords_invalidas(manager):
    login_page = manager.get(LoginPage)
    base = manager.base

    for pwd in PASSWORDS_INVALIDAS:
        login_page.go_to_login()
        assert not base.detect_http_500(), "Error 500 al cargar la pantalla de login."

        login_page.login(config.DEFAULT_USER, pwd or "")
        assert not base.detect_http_500(), "Error 500 después de enviar el formulario."
        assert not login_page.is_logged_in(), f"La contraseña '{pwd}' permitió el acceso."

        error = login_page.get_error_notification()
        if not error or "Completa este campo" in error:
            assert login_page.is_on_login_page(), f"La contraseña '{pwd}' cambió de pantalla sin mostrar error."
            continue
        assert error, f"La contraseña '{pwd}' no fue rechazada ni mostró notificación."
