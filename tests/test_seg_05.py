import pytest
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By

from helpers import config
from pages.account.profile_page import ProfilePage
from pages.login_page import LoginPage

WEAK_PASSWORD = "pass1234"  # Lacks uppercase and special chars
SUCCESS_TOAST = "Contraseña actualizada correctamente."
VALIDATION_KEYWORDS = (
    "minimo 8",
    "mínimo 8",
    "mayuscula",
    "mayúscula",
    "minuscula",
    "minúscula",
    "numero",
    "número",
    "caracter especial",
    "carácter especial",
    "contraseña inválida",
    "contraseña invalida",
)
STRONG_FALLBACK = f"{config.PROFILE_PASSWORD}"


@pytest.mark.no_profile
def test_seg_05_actualizar_contrasena_validando_formato(manager):
    login_page = manager.get(LoginPage)
    login_page.logout_and_clear()
    password_options = []
    if config.PROFILE_PASSWORD_OTHER:
        password_options.append(config.PROFILE_PASSWORD_OTHER)
    if config.PROFILE_PASSWORD not in password_options:
        password_options.append(config.PROFILE_PASSWORD)

    current_password = None
    for candidate in password_options:
        login_page.logout_and_clear()
        try:
            login_page.ensure_logged_in(
                config.PROFILE_USER,
                candidate,
                auto_two_factor=True,
            )
            current_password = candidate
            break
        except RuntimeError as exc:
            message = str(exc).lower()
            if "credenciales" in message and candidate != password_options[-1]:
                continue
            raise

    if not current_password:
        pytest.fail("No fue posible autenticar al usuario de perfil con las credenciales configuradas.")

    profile_page = manager.get(ProfilePage)
    password_changed = False
    strong_password = config.PROFILE_PASSWORD if current_password != config.PROFILE_PASSWORD else STRONG_FALLBACK

    def _restore_password(source_password: str):
        profile_page.open()
        profile_page.update_password(
            current=source_password,
            new=config.PROFILE_PASSWORD,
            confirm=config.PROFILE_PASSWORD,
        )
        profile_page.get_last_notification()

    try:
        profile_page.open()
        assert not manager.base.detect_http_500(), "La pantalla de perfil presentó un error 500."

        profile_page.update_password(
            current=current_password,
            new=WEAK_PASSWORD,
            confirm=WEAK_PASSWORD,
        )
        weak_notification = profile_page.get_last_notification().strip()
        try:
            manager.base.wait_for_condition(lambda _: profile_page.has_error_messages(), timeout=5, poll_frequency=0.2)
            weak_error = True
        except TimeoutException:
            weak_error = profile_page.has_error_messages()
        if not weak_error:
            try:
                body_text = profile_page.driver.find_element(By.TAG_NAME, "body").text.lower()
            except Exception:
                body_text = ""
            weak_error = any(keyword in body_text for keyword in VALIDATION_KEYWORDS)
        try:
            submit_button = profile_page.wait_for_locator(ProfilePage._submit_button, "visible", timeout=2)
            submit_state = (submit_button.text or "").strip().lower()
        except Exception:
            submit_state = ""

        weak_success = SUCCESS_TOAST.lower() in weak_notification.lower() or "guardando" in submit_state

        if weak_success and not weak_error:
            _restore_password(WEAK_PASSWORD)
            pytest.fail("El sistema aceptó una contraseña débil; la contraseña original fue restaurada.")

        assert weak_error or weak_notification, "No se mostró validación al intentar registrar una contraseña débil pero aun asi la guarda."

        profile_page.open()
        profile_page.update_password(
            current=current_password,
            new=strong_password,
            confirm=strong_password,
        )
        success_message = profile_page.get_last_notification().strip()
        assert success_message == SUCCESS_TOAST, "No apareció el mensaje esperado tras guardar la contraseña válida."
        password_changed = True
        current_password = strong_password

    finally:
        if password_changed and strong_password != config.PROFILE_PASSWORD:
            _restore_password(current_password)
