import re
import time
import requests
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select

from pages.base import Base
from helpers import config


class MaintenanceResourcesPage(Base):
    _add_button = (
        By.CSS_SELECTOR,
        "button[data-modal-toggle='static-modal'], button[data-modal-target='static-modal']",
    )
    _field_name = (By.NAME, "nombre")
    _select_state = (By.ID, "activo")
    _save_button = (By.CSS_SELECTOR, "button[type='submit'][form='recurso-form']")
    _notification = (By.CSS_SELECTOR, "div.notyf__message")
    _filter_name = (By.ID, "nombre-filter")
    _filters_button = (By.CSS_SELECTOR, "button[data-tooltip-target='tooltip-aplicar-filtros']")
    _import_button = (By.XPATH, "//button[contains(normalize-space(),'Importar datos')]")
    _import_modal = (By.ID, "static-modal-excel")
    _import_file = (By.ID, "excel_file")
    _import_save = (By.CSS_SELECTOR, "button[type='submit'][form='import-excel-recursos']")
    _paginator = (By.XPATH, "//p[contains(normalize-space(),'de un total de')]")
    _table_rows = (By.CSS_SELECTOR, "table tbody tr")
    _download_template_link = (
        By.XPATH,
        "//a[contains(@href, '.xls') and "
        "(contains(translate(normalize-space(.), 'ÁÉÍÓÚáéíóú', 'AEIOUaeiou'), 'DESCARGAR') "
        "or contains(translate(normalize-space(.), 'ÁÉÍÓÚáéíóú', 'AEIOUaeiou'), 'FORMATO') "
        "or contains(translate(normalize-space(.), 'ÁÉÍÓÚáéíóú', 'AEIOUaeiou'), 'PLANTILLA'))]",
    )
    _download_template_button = (By.ID, "descargarRecursosBtn")

    def open_add_modal(self):
        locators = [
            self._add_button,
            (By.ID, "add-button"),
            (By.CSS_SELECTOR, "button[data-modal-toggle*='recurso']"),
            (By.XPATH, "//button[contains(translate(., 'ÁÉÍÓÚ', 'AEIOU'), 'RECURSO')]"),
        ]
        btn = self.wait_for_any_locator(locators, "clickable")
        self.scroll_into_view(btn)
        self.safe_click(btn)

    def fill_form(self, name: str, active_value: str = "1"):
        self.type_into(self._field_name, name)
        select = Select(self.wait_for_locator(self._select_state, "visible"))
        select.select_by_value(active_value)
        time.sleep(0.25)

    def save_resource(self):
        btn = self.wait_for_locator(self._save_button, "clickable")
        self.scroll_into_view(btn)
        self.safe_click(btn)

    def get_notification(self):
        try:
            return self.wait_for_locator(self._notification, "visible").text.strip()
        except TimeoutException:
            return ""

    def filter_by_name(self, name: str):
        campo = self.wait_for_locator(self._filter_name, "visible")
        campo.clear()
        campo.send_keys(name)
        time.sleep(0.25)

    def apply_filters(self):
        btn = self.wait_for_locator(self._filters_button, "clickable")
        self.scroll_into_view(btn)
        self.safe_click(btn)
        self.pause_for_visual(2)

    def table_contains_resource(self, name: str) -> bool:
        lower = name.lower()
        locator = (
            By.XPATH,
            f"//table//td[contains(translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{lower}')]",
        )
        try:
            self.wait_for_locator(locator, "presence")
            return True
        except TimeoutException:
            return False

    def table_is_visible(self) -> bool:
        try:
            self.wait_for_locator((By.CSS_SELECTOR, "table"), "visible")
            return True
        except TimeoutException:
            return False

    def open_import_modal(self):
        button = self.wait_for_locator(self._import_button, "clickable")
        self.scroll_into_view(button)
        self.safe_click(button)
        self.wait_for_locator(self._import_modal, "visible", timeout=15)

    def upload_import_file(self, path: str):
        campo = self.wait_for_locator(self._import_file, "presence", timeout=10)
        campo.send_keys(path)

    def confirm_import(self):
        boton = self.wait_for_locator(self._import_save, "clickable", timeout=10)
        self.safe_click(boton)
        self.wait_for_page_ready(timeout=15)

    def refresh_table(self):
        self.driver.refresh()
        self.wait_for_page_ready(timeout=10)

    def get_total_results(self) -> int:
        texto = self.wait_for_locator(self._paginator, "visible", timeout=10).text
        match = re.search(r"de un total de\s+(\d+)", texto)
        if not match:
            raise AssertionError(f"No fue posible leer el total de resultados en: {texto}")
        return int(match.group(1))

    def get_visible_rows(self) -> int:
        return len(self.driver.find_elements(*self._table_rows))

    def download_template(self) -> tuple[str, bytes]:
        """Descarga la plantilla oficial para importar datos de recursos.

        La vista ofrece un enlace que en algunos ambientes puede tardar en ser visible
        u ocultarse tras menús. Para evitar bloqueos por sincronización se intenta leer
        el href cuando esté disponible y, si no, se usa el endpoint conocido.
        """
        self.wait_for_page_ready(timeout=10)
        endpoint = f"{config.BASE_URL}/descargar/archivo/recursos"
        clicked_href = ""
        button_clicked = False
        try:
            button = self.wait_for_locator(self._download_template_button, "clickable", timeout=5)
            self.scroll_into_view(button)
            try:
                self.safe_click(button)
            except TimeoutException:
                self.driver.execute_script("arguments[0].click();", button)
            button_clicked = True
            self.pause_for_visual(0.5)
        except TimeoutException:
            pass
        try:
            link = self.wait_for_locator(self._download_template_link, "presence", timeout=5)
            href = link.get_attribute("href") or ""
            self.scroll_into_view(link)
            try:
                clickable = self.wait_for_locator(self._download_template_link, "clickable", timeout=2)
                self.safe_click(clickable)
            except TimeoutException:
                # El enlace no se pudo clickear directamente, lo intentamos via JS.
                self.driver.execute_script("arguments[0].click();", link)
            clicked_href = href
            if clicked_href:
                if clicked_href.startswith("/"):
                    endpoint = f"{config.BASE_URL}{clicked_href}"
                else:
                    endpoint = clicked_href
        except TimeoutException:
            # No se encontró el enlace; continuamos con el endpoint por defecto.
            pass

        session = requests.Session()
        user_agent = self.driver.execute_script("return navigator.userAgent") or "Mozilla/5.0"
        headers = {
            "User-Agent": user_agent,
            "Referer": self.driver.current_url,
            "Accept": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet,application/vnd.ms-excel,application/octet-stream;q=0.9,*/*;q=0.8",
        }
        for cookie in self.driver.get_cookies():
            session.cookies.set(cookie["name"], cookie["value"])

        response = session.get(endpoint, headers=headers, timeout=60)
        response.raise_for_status()

        file_name = "formato_recursos.xlsx"
        disposition = response.headers.get("Content-Disposition") or ""
        if "filename=" in disposition:
            file_name = disposition.split("filename=")[-1].strip(' \";')

        if not response.content:
            raise AssertionError("El archivo descargado está vacío.")

        return file_name, response.content
