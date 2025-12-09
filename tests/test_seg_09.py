import json
import pytest

from helpers import config
from pages.login_page import LoginPage
from pages.navigation import NavigationMenu

MIXED_CONTENT_KEYWORD = "mixed content"


@pytest.mark.no_profile
def test_seg_09_forced_https_and_no_mixed_content(manager):
    login_page = manager.get(LoginPage)
    navigation = manager.get(NavigationMenu)

    http_base = config.BASE_URL.replace("https://", "http://")
    login_page.open_page(url=http_base, force_reload=True)
    final_url = (login_page.driver.current_url or "").lower()
    assert final_url.startswith("https://"), (
        f"La redirección a HTTPS falló. URL final: {login_page.driver.current_url}"
    )

    redirect_count = login_page.driver.execute_script(
        "try {var perf = performance.getEntriesByType('navigation')[0]; return perf ? perf.redirectCount : 0;} catch(e) {return 0;}"
    )
    assert redirect_count or http_base.rstrip("/") != final_url.rstrip("/"), (
        "No se detectó redirección 301/302 hacia HTTPS."
    )

    login_page.ensure_logged_in(
        config.MAINTENANCE_USER,
        config.MAINTENANCE_PASSWORD,
        auto_two_factor=True,
    )

    def _assert_page_secure(context: str):
        current = login_page.driver.current_url or ""
        assert current.startswith("https://"), f"La página {context} no está bajo HTTPS: {current}"
        is_secure = login_page.driver.execute_script("return window.isSecureContext === true;")
        assert is_secure, f"El contexto seguro del navegador no está activo en {context}."

        console_logs = []
        try:
            console_logs = login_page.driver.get_log("browser")
        except Exception:
            console_logs = []
        console_mixed = [
            entry for entry in console_logs if MIXED_CONTENT_KEYWORD in (entry.get("message", "").lower())
        ]
        assert not console_mixed, f"Se detectaron mensajes de mixed content en {context}: {console_mixed}"

        network_logs = []
        try:
            network_logs = login_page.driver.get_log("performance")
        except Exception:
            network_logs = []
        mixed_from_network = []
        for entry in network_logs:
            try:
                message = entry.get("message", "")
                data = json.loads(message)
                url = data.get("message", {}).get("params", {}).get("request", {}).get("url", "")
            except Exception:
                url = ""
            if isinstance(url, str) and url.startswith("http://"):
                mixed_from_network.append(url)
        assert not mixed_from_network, f"Se detectó contenido mixto en recursos de {context}: {mixed_from_network}"

        resource_urls = login_page.driver.execute_script(
            "try {return (performance.getEntriesByType('resource') || []).map(r => r.name)} catch(e) {return []}"
        )
        insecure_resources = [
            url for url in resource_urls if isinstance(url, str) and url.lower().startswith("http://")
        ]
        assert not insecure_resources, f"Recursos inseguros detectados en {context}: {insecure_resources}"

    modules = [
        ("Dashboard", lambda: login_page.open_page(url=config.HOME_URL, force_reload=True)),
        ("Recursos Humanos - Empleados", navigation.go_to_hr_employees),
        ("Reportes - Listado General", navigation.go_to_reports_list),
    ]

    for context, action in modules:
        action()
        login_page.wait_for_page_ready(timeout=5)
        _assert_page_secure(context)
