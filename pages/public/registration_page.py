from selenium.common.exceptions import InvalidElementStateException, TimeoutException, StaleElementReferenceException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

from helpers import config
from pages.base import Base


class RegistrationPage(Base):
    _register_link = (By.CSS_SELECTOR, "a[href*='/registrarse']")
    _name_input = (By.NAME, "nombre")
    _last_name_input = (By.NAME, "apellido")
    _birthdate_input = (By.NAME, "fecha_nacimiento")
    _school_select = (By.NAME, "escuela")
    _phone_input = (By.NAME, "telefono")
    _submit_button = (By.CSS_SELECTOR, "form button[type='submit']")
    _carnet_locators = [
        (By.NAME, "carnet"),
        (By.ID, "carnet"),
        (By.CSS_SELECTOR, "input[name*='carnet']"),
    ]
    _email_locators = [
        (By.NAME, "correo"),
        (By.ID, "correo"),
        (By.NAME, "email"),
        (By.CSS_SELECTOR, "input[type='email']"),
    ]
    _password_locators = [
        (By.NAME, "password"),
        (By.CSS_SELECTOR, "input[type='password']"),
    ]
    _confirm_password_locators = [
        (By.NAME, "password_confirmation"),
        (By.NAME, "password-confirmation"),
        (By.CSS_SELECTOR, "input[data-confirm='password']"),
    ]
    _error_messages_selector = (
        By.CSS_SELECTOR,
        ".notyf__message, .text-red-500, .text-red-600, .text-danger, [role='alert']",
    )
    _email_input = None
    _password_input = None
    _confirm_input = None
    _carnet_input = None

    def open(self):
        try:
            self.open_page(url=config.BASE_URL, force_reload=True)
            link = self.wait_for_locator(self._register_link, "clickable", timeout=10)
            self.scroll_into_view(link)
            self.safe_click(link)
        except TimeoutException:
            self.open_page(url=f"{config.BASE_URL}/registrarse")
        self.wait_for_url_contains("/registrarse")
        self.wait_for_locator(self._name_input, "visible")
        self.prepare_account_section()

    def fill_personal_data(self, nombre: str, apellido: str, fecha: str, escuela_value: str, telefono: str):
        self.type_into(self._name_input, nombre)
        self.type_into(self._last_name_input, apellido)
        campo_fecha = self.wait_for_locator(self._birthdate_input, "visible")
        self.driver.execute_script(
            "arguments[0].value = arguments[1]; arguments[0].dispatchEvent(new Event('input', {bubbles: true}));",
            campo_fecha,
            fecha,
        )
        select = self.wait_for_locator(self._school_select, "visible")
        self.driver.execute_script(
            "arguments[0].value = arguments[1]; arguments[0].dispatchEvent(new Event('change', {bubbles: true}));",
            select,
            escuela_value,
        )
        self.type_into(self._phone_input, telefono)

    def prepare_account_section(self):
        self._email_input = self._get_cached_input("_email_input", self._email_locators)
        try:
            self._password_input = self._get_cached_input("_password_input", self._password_locators)
        except TimeoutException:
            self._password_input = None
        try:
            self._confirm_input = self._get_cached_input("_confirm_input", self._confirm_password_locators)
        except TimeoutException:
            self._confirm_input = None
        try:
            self._carnet_input = self._get_cached_input("_carnet_input", self._carnet_locators)
        except TimeoutException:
            self._carnet_input = None

    def _get_cached_input(self, attr_name: str, locators):
        element = getattr(self, attr_name, None)
        if element:
            try:
                element.is_enabled()
                return element
            except StaleElementReferenceException:
                setattr(self, attr_name, None)
        element = self.wait_for_any_locator(locators, "visible", timeout=5)
        setattr(self, attr_name, element)
        return element

    def _set_control_value(self, element, value: str):
        script = """
            if (arguments[0].readOnly) { arguments[0].readOnly = false; }
            arguments[0].value = arguments[1] || '';
            arguments[0].dispatchEvent(new Event('input', { bubbles: true }));
            arguments[0].dispatchEvent(new Event('change', { bubbles: true }));
        """
        self.driver.execute_script(script, element, value or "")

    def fill_account_credentials(self, carnet: str | None, email: str, password: str):
        email = email or ""
        correo_input = self._get_cached_input("_email_input", self._email_locators)
        self._set_control_value(correo_input, email)

        carnet = carnet or ""
        if carnet:
            carnet_input = self._get_cached_input("_carnet_input", self._carnet_locators)
            self._set_control_value(carnet_input, carnet)

        password_input = self._get_cached_input("_password_input", self._password_locators)
        self._set_control_value(password_input, password)

        try:
            confirm_input = self._get_cached_input("_confirm_input", self._confirm_password_locators)
            self._set_control_value(confirm_input, password)
        except TimeoutException:
            pass

    def clear_account_inputs(self):
        if self._email_input:
            self._set_control_value(self._email_input, "")
        if self._password_input:
            self._set_control_value(self._password_input, "")
        if self._confirm_input:
            self._set_control_value(self._confirm_input, "")

    def submit(self):
        self.click_locator(self._submit_button)

    def has_validation_error(self) -> bool:
        invalid_count = self.driver.execute_script(
            "return document.querySelectorAll('input:invalid, select:invalid, textarea:invalid').length;"
        )
        if invalid_count and int(invalid_count) > 0:
            return True
        for notif in self.driver.find_elements(By.CSS_SELECTOR, ".notyf__message, .text-red-500, .text-red-600"):
            try:
                if notif.is_displayed() and notif.text.strip():
                    return True
            except Exception:
                continue
        body_text = self.driver.find_element(By.TAG_NAME, "body").text.lower()
        keywords = ("por favor", "debes", "obligatorio", "completa", "ingresa", "campo")
        return any(k in body_text for k in keywords)

    def get_password_error(self) -> str:
        errors = self.driver.find_elements(*self._error_messages_selector)
        for error in errors:
            try:
                texto = error.text.strip()
            except Exception:
                continue
            if not texto:
                continue
            lower = texto.lower()
            if "contraseña" in lower or "contrasena" in lower:
                return texto
        try:
            body_text = self.driver.find_element(By.TAG_NAME, "body").text.strip()
        except Exception:
            body_text = ""
        if body_text:
            lower_body = body_text.lower()
            if "contraseña" in lower_body or "contrasena" in lower_body:
                return body_text
        return ""

    def wait_for_password_error(self, timeout: int = 10) -> str:
        wait = WebDriverWait(self.driver, timeout)

        def _check(_driver):
            mensaje = self.get_password_error()
            return mensaje or False

        try:
            return wait.until(_check)
        except TimeoutException:
            return ""
