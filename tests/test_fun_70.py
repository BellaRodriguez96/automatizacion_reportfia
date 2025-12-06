from helpers import config
from pages.login_page import LoginPage


def test_fun_70_login_contrasena_incorrecta(manager):
    login_page = manager.get(LoginPage)
    login_page.logout_and_clear()
    login_page.go_to_login(force=True)

    login_page.login(config.FUNDS_USER, "ClaveIncorrecta!123")
    state, message = login_page.wait_for_auth_state(timeout=20)

    assert state == "error", "El sistema no mostró el mensaje de error esperado."
    normalized_message = (message or "").lower()
    esperado = "estas credenciales no coinciden con nuestros registros."
    equivalencia_valida = (
        esperado in normalized_message
        or ("credenciales" in normalized_message and "no coinciden" in normalized_message and "registros" in normalized_message)
    )
    assert equivalencia_valida, f"No se mostró el mensaje esperado. Recibido: {message!r}"
    assert not login_page.is_logged_in(), "El sistema permitió el acceso con credenciales inválidas."
    assert not manager.base.detect_http_500(), "Se mostró una página de error 500 en el intento de login."
