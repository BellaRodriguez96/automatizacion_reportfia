from pages.base import Base
from selenium.webdriver.common.by import By

class HomePage(Base):
    # Selectores de la página de Inicio.
    loginButton_str = "Iniciar sesión"
    signUpButton_str = "Registrarse"

    # Constructor de la página de Login.
    def __init__(self, driver):
        super().__init__(driver)

    # Métodos get que retornan los elementos WebElement.
    def get_loginButton(self):
        return self.wait_for_locator((By.LINK_TEXT, self.loginButton_str), "visible")

    def get_signUpButton(self):
        return self.wait_for_locator((By.LINK_TEXT, self.signUpButton_str), "visible")
