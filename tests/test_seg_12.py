import string

import pytest

from helpers import config
from pages.login_page import LoginPage
from pages.two_factor_page import TwoFactorPage


@pytest.mark.clean_profile
def test_seg_12_recordarme(manager):
    login_page = manager.get(LoginPage)
    login_page.go_to_login(force=True)
    login_page.set_remember_me(True)
    login_page.login(config.FUNDS_USER, config.FUNDS_PASSWORD)
    if login_page.requires_two_factor():
        two_factor = manager.get(TwoFactorPage)
        two_factor.complete_two_factor_flow(config.FUNDS_USER)

    assert login_page.is_logged_in(), "No se pudo iniciar sesión con recordarme activo."
    remember_cookie = login_page.get_remember_cookie()
    assert remember_cookie, "No se generó la cookie de recordarme."
    cookie_value = remember_cookie["value"] or ""
    assert cookie_value and all(ch in string.printable for ch in cookie_value), (
        "El valor de la cookie es ilegible o vacío."
    )
    lower_value = cookie_value.lower()
    assert config.FUNDS_USER.lower() not in lower_value, "La cookie contiene el usuario en texto plano."
    assert config.FUNDS_PASSWORD.lower() not in lower_value, "La cookie contiene la contraseña en texto plano."

    manager.quit()
    manager.start_driver(reset_profile=False, use_profile=manager.use_profile)

    relogin_page = manager.get(LoginPage)
    relogin_page.open_page(url=config.HOME_URL, force_reload=True)

    assert relogin_page.is_logged_in(), "La sesión no se mantuvo tras cerrar el navegador."
    assert not relogin_page.is_on_login_page(), "Se solicitó nuevamente autenticación pese a recordarme."
    relogin_page.logout_and_clear()
