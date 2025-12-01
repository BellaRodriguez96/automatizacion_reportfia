import random
import time

from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By

from pages.base import Base


class ReportsRegisterPage(Base):
    _incident_input = (By.ID, "search-id_tipo_incidencia")
    _incident_menu = (By.XPATH, "//div[contains(@class,'relative')]//ul")
    _incident_items = (By.XPATH, "//div[contains(@class,'relative')]//ul//li[normalize-space()]")
    _description_field = (By.ID, "descripcion")
    _location_input = (By.ID, "lugar-input")
    _location_items = (By.CSS_SELECTOR, "ul li")
    _file_input = (By.ID, "comprobantes")
    _send_button = (By.XPATH, "//button[contains(., 'Enviar reporte')]")
    _confirm_button = (By.XPATH, "//div[@id='send-modal']//button[@type='submit']")
    _notification = (By.CSS_SELECTOR, "div.notyf__message")

    def select_random_incident(self) -> str:
        campo = self.wait_for_locator(self._incident_input, "clickable")
        campo.click()
        campo.send_keys(" ")
        time.sleep(0.25)
        self.wait_for_locator(self._incident_menu, "visible")
        opciones = [
            li for li in self.find_all(self._incident_items)
            if li.text.strip()
        ]
        if not opciones:
            raise TimeoutException("No hay incidencias visibles para seleccionar.")
        opcion = random.choice(opciones)
        texto = opcion.text.strip()
        self.scroll_into_view(opcion)
        self.safe_click(opcion)
        time.sleep(0.25)
        return texto

    def set_description(self, descripcion: str):
        campo = self.wait_for_locator(self._description_field, "visible")
        campo.send_keys(descripcion)
        time.sleep(0.25)

    def select_random_location(self) -> str:
        campo = self.wait_for_locator(self._location_input, "clickable")
        campo.click()
        campo.send_keys(" ")
        time.sleep(0.25)
        opciones = [li for li in self.find_all(self._location_items) if li.text.strip()]
        if not opciones:
            raise TimeoutException("No existen lugares disponibles en el dropdown.")
        opcion = random.choice(opciones)
        texto = opcion.text.strip()
        self.driver.execute_script("arguments[0].value='';", campo)
        campo.send_keys(texto)
        time.sleep(0.25)
        destino = self.wait_for_locator((By.XPATH, f"//li[contains(., '{texto}')]"), "clickable")
        self.safe_click(destino)
        time.sleep(0.25)
        return texto

    def upload_evidence(self, path):
        self.driver.execute_script(
            "document.querySelectorAll('.file-input-overlay').forEach(function(el){el.remove();});"
        )
        posibles_locators = [
            (By.ID, "comprobantes"),
            (By.NAME, "comprobantes[]"),
            (By.CSS_SELECTOR, "input[type='file'][id*='comprob']"),
            (By.CSS_SELECTOR, "input[type='file']"),
        ]

        campo = None
        end_time = time.time() + self.default_timeout
        while time.time() < end_time and campo is None:
            for locator in posibles_locators:
                elementos = self.driver.find_elements(*locator)
                if elementos:
                    campo = elementos[0]
                    break
            if campo is None:
                time.sleep(0.2)

        if campo is None:
            raise TimeoutException("No se encontro el input de archivos (comprobantes).")

        self.driver.execute_script(
            "arguments[0].classList.remove('hidden'); arguments[0].style.display='block'; arguments[0].removeAttribute('multiple');",
            campo,
        )
        self.scroll_into_view(campo)
        campo.send_keys(str(path))
        time.sleep(0.25)

    def submit_report(self):
        enviar = self.wait_for_locator(self._send_button, "clickable")
        self.safe_click(enviar)
        confirmar = self.wait_for_locator(self._confirm_button, "clickable")
        self.safe_click(confirmar)
        try:
            mensaje = self.wait_for_locator(self._notification, "visible").text.strip()
        except TimeoutException:
            mensaje = ""
        finally:
            try:
                cerrar = self.wait_for_locator((By.CSS_SELECTOR, "button[data-modal-hide]"), "clickable")
                self.safe_click(cerrar)
            except TimeoutException:
                pass
        return mensaje

    def get_notification(self):
        try:
            return self.wait_for_locator(self._notification, "visible").text.strip()
        except TimeoutException:
            return ""
