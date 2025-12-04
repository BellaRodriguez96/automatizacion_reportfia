import pytest

from pages.login_page import LoginPage


@pytest.mark.no_profile
def test_fun_71_login_con_usuarios_inexistentes(manager):
    login_page = manager.get(LoginPage)
    usuarios = [
        ("usuario_no_registrado_1", "pass_invalida_1", 1),
        ("usuario_no_registrado_2", "pass_invalida_2", 1),
        ("usuario_no_registrado_3", "pass_invalida_3", 10),
    ]

    for usuario, contrasena, intentos in usuarios:
        for _ in range(intentos):
            login_page.go_to_login()
            login_page.login(usuario, contrasena)
            mensaje = login_page.get_error_notification()
            assert mensaje, "No se mostró el mensaje de error para credenciales inválidas."
            mensaje_lower = mensaje.lower()
            palabras_clave = ("credencial", "no coinciden", "intent", "acceso")
            assert any(palabra in mensaje_lower for palabra in palabras_clave)
