import pytest
from selenium.webdriver.common.by import By

from helpers import config
from pages.login_page import LoginPage


RESTRICTED_PATHS = (
    "/inicio",
    "/dashboard",
    "/admin",
    "/reportes",
)
INVALID_USER = "usuario.invalido@ues.edu.sv"
INVALID_PASSWORD = "ClaveErronea123!"
_HTTP_NOT_FOUND_TOKENS = ("404", "no encontrado", "no se encuentra")


@pytest.mark.clean_profile
def test_seg_19_acceso_sin_autenticacion(manager):
    manager.base.clear_storage()
    login_page = manager.get(LoginPage)
    login_page.logout_and_clear()

    for path in RESTRICTED_PATHS:
        target_url = f"{config.BASE_URL}{path}"
        login_page.open_page(url=target_url, force_reload=True)
        page_source = (login_page.driver.page_source or "").lower()
        contains_404 = any(token in page_source for token in _HTTP_NOT_FOUND_TOKENS)
        if contains_404:
            continue
        assert login_page.is_on_login_page(), f"La ruta {path} permitió acceso sin autenticación."
        assert not login_page.is_logged_in(), f"La ruta {path} abrió sesión sin credenciales."

    login_page.go_to_login(force=True)
    login_page.enter_text(login_page.get_user_input(), INVALID_USER)
    login_page.enter_text(login_page.get_password_input(), INVALID_PASSWORD)
    submit = login_page.wait_for_locator((By.XPATH, login_page.login_button_str), "clickable", timeout=5)
    login_page.safe_click(submit)
    login_page.wait_for_locator(login_page.notification_selector, "visible", timeout=6)

    assert login_page.is_on_login_page(), "El sistema permitió continuar con credenciales inválidas."
    error_message = login_page.get_error_notification()
    assert error_message, "No se mostró mensaje de acceso denegado con credenciales inválidas."
