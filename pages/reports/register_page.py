import random
import time
from pathlib import Path

from selenium.common.exceptions import (
    ElementClickInterceptedException,
    ElementNotInteractableException,
    NoSuchElementException,
    TimeoutException,
    WebDriverException,
)
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

    def select_incident_by_text(self, texto: str) -> str:
        campo = self.wait_for_locator(self._incident_input, "clickable")
        campo.click()
        self.driver.execute_script("arguments[0].value='';", campo)
        campo.send_keys(texto)
        opcion = self.wait_for_locator(
            (
                By.XPATH,
                f"//ul[contains(@class,'absolute')]//li[contains(normalize-space(), '{texto}')]",
            ),
            "clickable",
        )
        self.safe_click(opcion)
        time.sleep(0.25)
        return texto

    def select_location_by_text(self, texto: str) -> str:
        campo = self.wait_for_locator(self._location_input, "clickable")
        self.driver.execute_script("arguments[0].value='';", campo)
        campo.send_keys(texto)
        opcion = self.wait_for_locator(
            (
                By.XPATH,
                f"//div[contains(@class,'shadow-lg')]//li[.//span[normalize-space()='{texto}']]",
            ),
            "clickable",
        )
        self.safe_click(opcion)
        time.sleep(0.25)
        return texto

    def upload_evidence(self, path):
        archivo = Path(path).expanduser().resolve()
        if not archivo.exists():
            raise FileNotFoundError(f"No se encontro la evidencia a adjuntar: {archivo}")

        posibles_locators = [
            (By.ID, "comprobantes"),
            (By.NAME, "comprobantes[]"),
            (By.CSS_SELECTOR, "input[type='file'][id*='comprob']"),
            (By.CSS_SELECTOR, "input[type='file']"),
        ]

        last_error: Exception | None = None
        end_time = time.time() + self.default_timeout
        while time.time() < end_time:
            campo = self._find_first_input(posibles_locators)
            if not campo:
                time.sleep(0.2)
                continue
            try:
                self._prepare_input_for_upload(campo)
                campo.send_keys(str(archivo))
                self.wait_for_page_ready(timeout=5)
                return
            except (ElementNotInteractableException, ElementClickInterceptedException, WebDriverException) as exc:
                last_error = exc
                time.sleep(0.3)
                continue

        mensaje = "No se encontro un input de archivos interactuable."
        if last_error:
            mensaje = f"{mensaje} Ultimo error: {last_error}"
        raise TimeoutException(mensaje)

    def submit_report(self):
        enviar = self.wait_for_locator(self._send_button, "clickable")
        self.safe_click(enviar)
        confirmar = self.wait_for_locator(self._confirm_button, "clickable")
        self.safe_click(confirmar)
        try:
            mensaje = self.wait_for_locator(self._notification, "visible", timeout=8).text.strip()
        except TimeoutException:
            mensaje = ""
        finally:
            self._dismiss_success_modal()
        return mensaje

    def get_notification(self):
        try:
            return self.wait_for_locator(self._notification, "visible").text.strip()
        except TimeoutException:
            return ""

    def _dismiss_success_modal(self):
        try:
            botones = self.driver.find_elements(By.CSS_SELECTOR, "button[data-modal-hide]")
        except (NoSuchElementException, TimeoutException):
            return
        for boton in botones:
            try:
                if not boton.is_displayed():
                    continue
            except Exception:
                continue
            try:
                self.safe_click(boton)
            except Exception:
                try:
                    self.driver.execute_script("arguments[0].click();", boton)
                except Exception:
                    continue
            self.wait_for_page_ready(timeout=5)
            return

    def _find_first_input(self, locators):
        hidden_candidate = None
        for locator in locators:
            elementos = self.driver.find_elements(*locator)
            for elemento in elementos:
                try:
                    if elemento.is_displayed():
                        return elemento
                    hidden_candidate = hidden_candidate or elemento
                except Exception:
                    continue
        return hidden_candidate

    def _prepare_input_for_upload(self, element):
        self._remove_overlays()
        self.driver.execute_script(
            "arguments[0].classList.remove('hidden');"
            "arguments[0].style.display='block';"
            "arguments[0].removeAttribute('multiple');"
            "arguments[0].removeAttribute('disabled');",
            element,
        )
        self.scroll_into_view(element)

    def _remove_overlays(self):
        self.driver.execute_script(
            "document.querySelectorAll('.file-input-overlay, [data-overlay]').forEach(function(el){el.remove();});"
        )
