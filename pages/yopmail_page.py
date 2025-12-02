import re
import time

from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from helpers import config
from pages.base import Base


class YopmailPage(Base):
    """Interactúa con Yopmail para obtener códigos de 2FA."""

    _login_field = (By.ID, "login")
    _mail_iframe = (By.CSS_SELECTOR, "iframe#ifmail, iframe[name='ifmail']")
    _message_code = (By.CSS_SELECTOR, "#mail strong")

    def fetch_code(self, carnet: str) -> str:
        main_window = self.driver.current_window_handle
        self.driver.switch_to.window(main_window)

        # Abrir nueva pestaña al estilo del script original
        if not self.driver.window_handles:
            raise RuntimeError("No existe ninguna pestaña activa en Chrome.")

        self.driver.execute_script("window.open('about:blank', '_blank');")
        time.sleep(0.5)

        nueva_pestana = self.driver.window_handles[-1]
        self.driver.switch_to.window(nueva_pestana)
        self.driver.get(config.YOPMAIL_URL)

        try:
            campo = self.wait_for_locator(self._login_field, "visible", timeout=10)
            campo.clear()
            campo.send_keys(carnet)
            campo.send_keys(Keys.ENTER)
            time.sleep(1)

            iframe = self._wait_for_iframe()
            self.driver.switch_to.frame(iframe)

            code = None
            wait = WebDriverWait(self.driver, 60)  # Esperar hasta 1 minuto inicialmente
            try:
                code = wait.until(EC.visibility_of_element_located(self._message_code)).text.strip()
            except TimeoutException:
                time.sleep(30)  # Esperar 30 segundos adicionales
                try:
                    code = wait.until(EC.visibility_of_element_located(self._message_code)).text.strip()
                except TimeoutException:
                    cuerpo = self.driver.find_element(By.TAG_NAME, "body").text
                    match = re.search(r"\b\d{6}\b", cuerpo)
                    if match:
                        code = match.group(0)
            finally:
                self.driver.switch_to.default_content()

            if not code:
                raise TimeoutException("No se pudo encontrar el código 2FA en Yopmail tras múltiples intentos.")

            return code

        finally:
            # Asegurarse de cerrar la pestaña y volver a la ventana principal
            self.driver.close()
            self.driver.switch_to.window(main_window)

    def _wait_captcha_if_needed(self, wait_seconds: int = 60):
        """Si aparece un CAPTCHA, espera hasta 1 minuto para que se resuelva."""
        if not self._captcha_present():
            return
        deadline = time.time() + wait_seconds
        while time.time() < deadline:
            time.sleep(5)
            if not self._captcha_present():
                return
        if self._captcha_present():
            raise TimeoutException("El CAPTCHA de Yopmail no se resolvió tras esperar 60 segundos.")

    def _captcha_present(self) -> bool:
        try:
            captcha_locator = (
                By.CSS_SELECTOR,
                "iframe[title*='CAPTCHA' i], iframe[src*='captcha' i], div[id*='captcha' i]",
            )
            WebDriverWait(self.driver, 2).until(EC.presence_of_element_located(captcha_locator))
            return True
        except TimeoutException:
            return False

    def _wait_for_iframe(self):
        deadline = time.time() + 5
        while time.time() < deadline:
            frames = self.driver.find_elements(By.TAG_NAME, "iframe")
            for frame in frames:
                name = (frame.get_attribute("name") or "").lower()
                iframe_id = (frame.get_attribute("id") or "").lower()
                if name == "ifmail" or iframe_id == "ifmail":
                    return frame
            time.sleep(0.5)
        raise TimeoutException("No se encontró el iframe del correo (ifmail).")
