from pages.login_page import LoginPage


def test_fun_13_login_usuario_inactivo(manager):
    usuario_inactivo = "CMFUN13"
    password_inactivo = "vAVE8EKGGf0Vhrct"
    expected_message = "El usuario no se encuentra activo dentro del sistema"

    login_page = manager.get(LoginPage)
    login_page.logout_and_clear()
    login_page.go_to_login(force=True)

    login_page.login(usuario_inactivo, password_inactivo)
    state, message = login_page.wait_for_auth_state(timeout=25)

    assert state == "error", f"El sistema no mostro un error y respondio con estado '{state}'."
    assert message == expected_message, f"Mensaje mostrado inesperado: {message!r}"
    assert not login_page.requires_two_factor(), "El sistema intento avanzar al flujo de Two Factor para un usuario inactivo."
    assert not login_page.is_logged_in(), "El sistema permitio el acceso con un usuario inactivo."
    assert not manager.base.detect_http_500(), "Se detecto una pagina de error 500 durante el intento de login."
