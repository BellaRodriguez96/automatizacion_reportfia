import pytest

from helpers import config
from pages.login_page import LoginPage

PASSWORDS_INVALIDAS_BLOQUEO = ["Hl3oFfmQEethf7bx4"] * 10


@pytest.mark.clean_profile
def test_seg_17_bloqueo_por_fuerza_bruta(manager):
    login_page = manager.get(LoginPage)
    base = manager.base
    captcha_activado = False

    for intento, pwd in enumerate(PASSWORDS_INVALIDAS_BLOQUEO, start=1):
        login_page.go_to_login()
        assert not base.detect_http_500(), "Error 500 al cargar el login."

        login_page.login(config.DEFAULT_USER, pwd)
        assert not base.detect_http_500(), "Error 500 después de enviar el formulario."

        if intento >= 5 and login_page.has_security_lockdown():
            captcha_activado = True
            break

        error = login_page.get_error_notification()
        assert error, f"La contraseña '{pwd}' no generó mensaje de rechazo."

    assert captcha_activado, "No se activó bloqueo/CAPTCHA tras múltiples intentos fallidos."
