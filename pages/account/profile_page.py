from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By

from helpers import config
from pages.base import Base


class ProfilePage(Base):
    _password_form = (By.CSS_SELECTOR, "form[action$='/password']")
    _current_password = (By.ID, "update_password_current_password")
    _new_password = (By.ID, "update_password_password")
    _confirm_password = (By.ID, "update_password_password_confirmation")
    _submit_button = (By.CSS_SELECTOR, "form[action$='/password'] button[type='submit']")
    _notification = (By.CSS_SELECTOR, "div.notyf__message")
    _error_labels = (By.CSS_SELECTOR, ".text-red-600, .text-red-500, .text-sm.text-red-600")
    _password_section_triggers = [
        (By.CSS_SELECTOR, "[data-accordion-target*='password']"),
        (By.CSS_SELECTOR, "button[data-accordion-target='#accordion-sesion']"),
        (
            By.XPATH,
            "//button[contains(translate(normalize-space(.), 'áéíóúÁÉÍÓÚ', 'aeiouAEIOU'), 'CONTRASENA')]",
        ),
        (
            By.XPATH,
            "//a[contains(translate(normalize-space(.), 'áéíóúÁÉÍÓÚ', 'aeiouAEIOU'), 'CONTRASENA')]",
        ),
    ]

    def open(self):
        self.open_page(url=f"{config.BASE_URL}/perfil")
        self.wait_for_page_ready(timeout=15)
        if not self._ensure_password_section_visible():
            raise TimeoutException("No fue posible mostrar el formulario para actualizar la contraseña.")

    def update_password(self, current: str, new: str, confirm: str | None = None):
        confirm = confirm if confirm is not None else new
        self.type_into(self._current_password, current)
        self.type_into(self._new_password, new)
        self.type_into(self._confirm_password, confirm)
        submit = self.wait_for_locator(self._submit_button, "clickable")
        self.safe_click(submit)
        self.wait_for_page_ready(timeout=10)

    def get_last_notification(self) -> str:
        try:
            return self.wait_for_locator(self._notification, "visible", timeout=5).text.strip()
        except Exception:
            return ""

    def has_error_messages(self) -> bool:
        messages = []
        for element in self.driver.find_elements(*self._error_labels):
            try:
                text = element.text.strip()
            except Exception:
                continue
            if text:
                messages.append(text.lower())
        if messages:
            return True
        notification = self.get_last_notification().lower()
        keywords = ("diferente", "igual", "contrasena", "contraseña", "valida", "válida")
        return any(keyword in notification for keyword in keywords)

    def _ensure_password_section_visible(self) -> bool:
        if self._password_form_visible():
            return True
        try:
            trigger = self.wait_for_any_locator(self._password_section_triggers, "clickable", timeout=10)
        except TimeoutException:
            return False
        if trigger:
            self.scroll_into_view(trigger)
            self.safe_click(trigger)
        return self._password_form_visible()

    def _password_form_visible(self) -> bool:
        try:
            self.wait_for_locator(self._password_form, "visible", timeout=10)
            self.wait_for_locator(self._submit_button, "visible", timeout=10)
            return True
        except TimeoutException:
            return False
