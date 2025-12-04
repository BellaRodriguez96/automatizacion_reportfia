import os
from uuid import uuid4

from helpers import config
from helpers.file_factory import create_basic_excel
from pages.login_page import LoginPage
from pages.maintenance.resources_page import MaintenanceResourcesPage
from pages.navigation import NavigationMenu


def test_fun_52_importar_recursos_desde_excel(manager):
    login_page = manager.get(LoginPage)
    login_page.ensure_logged_in(config.MAINTENANCE_USER, config.MAINTENANCE_PASSWORD)

    navigation = manager.get(NavigationMenu)
    navigation.go_to_maintenance_resources()

    recursos = manager.get(MaintenanceResourcesPage)
    assert recursos.table_is_visible(), "No se cargó el listado de recursos."

    headers = ["Nombre", "Descripcion"]
    rows = [
        [f"Recurso QA {uuid4().hex[:5]}", "Generado desde FUN-52"],
        [f"Respaldo QA {uuid4().hex[:5]}", "Datos para importar"],
    ]
    archivo = create_basic_excel(headers, rows)

    try:
        recursos.open_import_modal()
        recursos.upload_import_file(str(archivo))
        recursos.confirm_import()
    finally:
        if os.path.exists(archivo):
            os.remove(archivo)

    mensaje = recursos.get_notification()
    recursos.refresh_table()
    assert mensaje, "No se recibió respuesta del sistema después de intentar importar recursos."
