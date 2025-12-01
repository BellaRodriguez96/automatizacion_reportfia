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

        campo = self.wait_for_locator(self._login_field, "visible")
        campo.clear()
        campo.send_keys(carnet)
        campo.send_keys(Keys.ENTER)
        time.sleep(0.5)

        iframe = self._wait_for_iframe()
        self.driver.switch_to.frame(iframe)

        code = None
        wait = WebDriverWait(self.driver, 5)
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
            raise TimeoutException("No se pudo encontrar el código 2FA en Yopmail.")

        self.driver.close()
        self.driver.switch_to.window(main_window)
        return code

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
