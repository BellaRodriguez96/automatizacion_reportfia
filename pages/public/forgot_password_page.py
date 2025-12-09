from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By

from helpers import config
from pages.base import Base


class ForgotPasswordPage(Base):
    _forgot_link = (By.CSS_SELECTOR, "a[href*='/forgot-password']")
    _forgot_text_link = (
        By.XPATH,
        "//a[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZÁÉÍÓÚÜ', 'abcdefghijklmnopqrstuvwxyzáéíóúü'), 'olvidaste tu contrase?a')]",
    )
    _email_input = (By.NAME, "email")
    _submit_button = (By.CSS_SELECTOR, "form button[type='submit']")
    _notification = (By.CSS_SELECTOR, "div.notyf__message, .alert, .toast-message")

    def open_from_login(self):
        if "forgot-password" in (self.driver.current_url or ""):
            self.wait_for_locator(self._email_input, "visible")
            return
        for locator in (self._forgot_link, self._forgot_text_link):
            try:
                self.click_locator(locator)
                self.wait_for_url_contains("forgot-password", timeout=5)
                self.wait_for_locator(self._email_input, "visible")
                return
            except TimeoutException:
                continue
        self.open_page(url=f"{config.BASE_URL}/forgot-password")
        self.wait_for_url_contains("forgot-password")
        self.wait_for_locator(self._email_input, "visible")

    def request_reset(self, email: str):
        campo = self.wait_for_locator(self._email_input, "visible")
        campo.clear()
        campo.send_keys(email)
        self.click_locator(self._submit_button)

    def has_error_message(self) -> bool:
        keywords = (
            "no existe",
            "no registrado",
            "no encontrado",
            "usuario no encontrado",
            "correo",
        )

        try:
            notif = self.wait_for_locator(self._notification, "visible", timeout=5)
            texto = notif.text.strip().lower()
            if any(k in texto for k in keywords):
                return True
        except TimeoutException:
            pass

        body_text = self.driver.find_element(By.TAG_NAME, "body").text.lower()
        return any(k in body_text for k in keywords)
