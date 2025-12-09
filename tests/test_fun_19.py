import uuid

from helpers import config
from pages.hr.entities_page import EntitiesPage
from pages.login_page import LoginPage
from pages.navigation import NavigationMenu


def test_fun_19_registrar_entidad(manager):
    nombre = f"Entidad QA {uuid.uuid4().hex[:6]}"
    login_page = manager.get(LoginPage)
    login_page.ensure_logged_in(config.MAINTENANCE_USER, config.MAINTENANCE_PASSWORD)

    navigation = manager.get(NavigationMenu)
    navigation.go_to_hr_entities()

    entidades = manager.get(EntitiesPage)
    entidades.wait_until_ready()

    entidades.filter_by_name(nombre)
    entidades.apply_filters()
    entidades.clear_filters()

    entidades.open_add_modal()
    descripcion = f"Entidad creada automáticamente {uuid.uuid4().hex[:8]}"
    entidades.fill_form(nombre, descripcion, activo=True)
    entidades.save()

    mensaje = entidades.get_notification()
    assert mensaje, "No se mostró confirmación después de registrar la entidad."

    entidades.filter_by_name(nombre)
    entidades.apply_filters()

    assert entidades.table_contains_entity(nombre), "La entidad no aparece en el listado después de guardarla."
    assert entidades.entity_has_status(nombre, "Activo"), "La entidad no muestra estado Activo en el listado."
