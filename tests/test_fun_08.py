import pytest

from helpers import config
from helpers.status_logger import log_failure, log_success
from pages.account.profile_page import ProfilePage
from pages.login_page import LoginPage


def _resolve_profile_passwords(login_page: LoginPage) -> tuple[str, str]:
    """Return (current_password, alternate_password) trying both configured values."""
    passwords: list[str] = []
    for candidate in (config.PROFILE_PASSWORD, config.PROFILE_PASSWORD_OTHER):
        if candidate and candidate not in passwords:
            passwords.append(candidate)

    if len(passwords) < 2:
        raise RuntimeError("Debe configurar PROFILE_PASSWORD y PROFILE_PASSWORD_OTHER con valores distintos.")

    last_error: str | None = None
    for idx, pwd in enumerate(passwords):
        alternate = passwords[(idx + 1) % len(passwords)]
        try:
            login_page.ensure_logged_in(config.PROFILE_USER, pwd)
            return pwd, alternate
        except RuntimeError as exc:
            last_error = str(exc)
            login_page.logout_and_clear()

    raise RuntimeError(f"No fue posible iniciar sesión con ninguna contraseña configurada. Último error: {last_error or 'desconocido'}")


@pytest.mark.clean_profile
def test_fun_08_contrasena_no_se_reutiliza(manager):
    login_page = manager.get(LoginPage)
    current_password, alternate_password = _resolve_profile_passwords(login_page)

    perfil = manager.get(ProfilePage)
    perfil.open()
    if manager.base.detect_http_500():
        log_failure("Se detectó un error 500 al intentar abrir el perfil.")
        pytest.fail("Pantalla de perfil mostró error 500.")

    perfil.update_password(current_password, current_password)
    if perfil.has_error_messages():
        log_success("El sistema evitó reutilizar la misma contraseña.")
    else:
        log_failure("El sistema permitió reutilizar la misma contraseña sin errores visibles.")
    assert perfil.has_error_messages(), "El sistema permitió reutilizar la misma contraseña sin mostrar errores."

    perfil.open()
    if manager.base.detect_http_500():
        log_failure("Se detectó un error 500 al reabrir el perfil.")
        pytest.fail("Pantalla de perfil mostró error 500.")

    perfil.update_password(current_password, alternate_password)
    mensaje = perfil.get_last_notification()
    if mensaje:
        log_success("La contraseña se actualizó correctamente con un valor diferente.")
    else:
        log_failure("No se mostró confirmación al actualizar la contraseña con un valor diferente.")
    assert mensaje, "No se mostró confirmación al actualizar la contraseña con un valor diferente."
