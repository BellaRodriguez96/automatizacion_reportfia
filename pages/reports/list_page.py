import time

from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select

from pages.base import Base


class ReportsListPage(Base):
    _filters_button = (By.CSS_SELECTOR, "button[data-tooltip-target='tooltip-aplicar-filtros']")
    _date_dropdown_button = (By.ID, "dropdownRadioButton")
    _date_dropdown = (By.ID, "dropdownRadio")
    _last_seven_days_option = (By.ID, "filter-radio-example-2")
    _today_option = (By.ID, "filter-radio-example-1")
    _type_search_input = (By.ID, "search-tipoIncidencia")
    _type_dropdown = (By.ID, "dropdown-tipoIncidencia")
    _status_select = (By.ID, "estado")
    _register_link = (By.XPATH, "//a[contains(@href,'/reportes/registrar')]")

    def open_date_dropdown(self):
        self.click_locator(self._date_dropdown_button)
        self.wait_for_locator(self._date_dropdown, "visible")

    def select_last_seven_days(self):
        self.open_date_dropdown()
        self.click_locator(self._last_seven_days_option)

    def select_today(self):
        self.open_date_dropdown()
        self.click_locator(self._today_option)

    def filter_by_incident_text(self, texto: str):
        campo = self.wait_for_locator(self._type_search_input, "clickable")
        self.scroll_into_view(campo)
        campo.click()
        campo.clear()
        campo.send_keys(texto)
        time.sleep(0.25)
        self.wait_for_locator(self._type_dropdown, "visible")
        opciones = self.find_all((By.CSS_SELECTOR, "#dropdown-tipoIncidencia li"))
        if not opciones:
            raise TimeoutException("No se encontraron opciones en el dropdown de tipo de incidencia.")
        opcion = next((opt for opt in opciones if texto.lower() in opt.text.strip().lower()), opciones[0])
        self.safe_click(opcion)
        time.sleep(0.25)

    def filter_by_state(self, estado: str):
        select_element = self.wait_for_locator(self._status_select, "visible")
        select = Select(select_element)
        select.select_by_visible_text(estado)
        time.sleep(0.25)

    def apply_filters(self):
        btn = self.wait_for_locator(self._filters_button, "clickable")
        self.scroll_into_view(btn)
        self.safe_click(btn)
        self.pause_for_visual(2)

    def open_register_form(self):
        self.click_locator(self._register_link)
