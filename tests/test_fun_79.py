import pytest

from pages.login_page import LoginPage
from pages.public.forgot_password_page import ForgotPasswordPage

TEST_EMAIL = "AL180444@ues.edu.sv"


@pytest.mark.no_profile
def test_fun_79_recuperacion_correo_no_registrado(manager):
    login_page = manager.get(LoginPage)
    login_page.go_to_login()

    forgot_page = manager.get(ForgotPasswordPage)
    forgot_page.open_from_login()
    forgot_page.request_reset(TEST_EMAIL)

    assert forgot_page.has_error_message(), "No se mostró error al solicitar recuperación con un correo no registrado."
