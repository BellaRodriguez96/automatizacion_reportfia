import random
from datetime import datetime
import time

import pytest

from pages.public.registration_page import RegistrationPage

TEST_DATA = {
    "nombre": "PRUEBA",
    "apellido": "AUTOMATIZADA",
    "escuela_value": "2",
}

WEAK_PASSWORDS = [
    "123",
    "12345678",
    "admin123",
    "password",
    ".admin",
    "123456789",
]


def _random_birthdate():
    year = random.randint(1940, 1959)
    month = random.randint(1, 12)
    day = random.randint(1, 28)
    return datetime(year, month, day).strftime("%d/%m/%Y")


def _generate_student_email():
    decade = random.randint(40, 59)
    suffix = random.randint(0, 999)
    email = f"aa{decade}{suffix:03d}@ues.edu.sv"
    return email


def _random_phone():
    first = random.randint(100, 999)
    second = random.randint(1000, 9999)
    return f"+503 7{first} {second}"


@pytest.mark.no_profile
def test_fun_76_validacion_contrasenas_debiles(manager):
    registro = manager.get(RegistrationPage)
    registro.open()
    registro.fill_personal_data(
        TEST_DATA["nombre"],
        TEST_DATA["apellido"],
        _random_birthdate(),
        TEST_DATA["escuela_value"],
        _random_phone(),
    )
    email = _generate_student_email()

    for password in WEAK_PASSWORDS:
        time.sleep(2)
        registro.clear_account_inputs()
        registro.fill_account_credentials(None, email, password)
        registro.submit()

        error_text = registro.wait_for_password_error(timeout=15)
        assert error_text, f"La contraseña débil '{password}' fue aceptada inesperadamente."
        lower_text = error_text.lower()
        assert "contraseña" in lower_text or "contrasena" in lower_text, (
            f"No se mostró mensaje de requisitos mínimos para '{password}'. Mensaje recibido: {error_text!r}"
        )
        registro.wait_for_url_contains("/registrarse")
