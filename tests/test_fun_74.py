import pytest

from pages.public.registration_page import RegistrationPage

TEST_DATA = {
    "nombre": "PRUEBA",
    "apellido": "AUTOMATIZADA",
    "fecha_nacimiento": "15/11/1996",
    "escuela_value": "2",
    "telefono": "6666666",
}


@pytest.mark.no_profile
def test_fun_74_registro_campos_vacios(manager):
    registro = manager.get(RegistrationPage)
    registro.open()

    registro.fill_personal_data(
        TEST_DATA["nombre"],
        TEST_DATA["apellido"],
        TEST_DATA["fecha_nacimiento"],
        TEST_DATA["escuela_value"],
        TEST_DATA["telefono"],
    )

    registro.submit()
    assert registro.has_validation_error(), "No se mostró mensaje de validación al dejar campos obligatorios vacíos."
