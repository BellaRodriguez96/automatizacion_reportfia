from helpers import config
from pages.login_page import LoginPage
from pages.maintenance.resources_page import MaintenanceResourcesPage
from pages.navigation import NavigationMenu


def test_fun_51_descargar_formato_importacion(manager):
    login_page = manager.get(LoginPage)
    login_page.ensure_logged_in(config.MAINTENANCE_USER, config.MAINTENANCE_PASSWORD)

    navigation = manager.get(NavigationMenu)
    navigation.go_to_maintenance_resources()

    recursos = manager.get(MaintenanceResourcesPage)
    assert recursos.table_is_visible(), "No se cargó el módulo de recursos."

    archivo, contenido = recursos.download_template()

    assert archivo.lower().endswith((".xlsx", ".xls")), "El formato descargado no es un archivo Excel."
    tokens = ("formato", "plantilla", "recurso")
    assert any(token in archivo.lower() for token in tokens), "El nombre del archivo no coincide con la plantilla oficial."
    assert contenido and len(contenido) > 0, "El archivo descargado está vacío."
