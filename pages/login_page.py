from pages.base import Base
from selenium.webdriver.common.by import By

class LoginPage(Base):
    # Selectores de la página de Inicio.
    ues_logo_str = "h-36"
    user_input_str = "carnet"
    password_input_str = "password"
    checkbox_str = "remember_me"
    forgot_password_str = "Olvidaste tu contraseña"
    login_button_str = "//*[@type = \"submit\"]"
    back_button_str = "h-4"

    # Constructor de la página de Login.
    def __init__(self, driver):
        """
        Constructor de la página de Home de instancia de WebDriver.
        """
        self.driver = driver

    # Métodos get que retornan los elementos WebElement.
    def get_logo(self):
        return self.driver.find_element(By.CLASS_NAME, self.ues_logo_str)
    
    def get_user_input(self):
        return self.driver.find_element(By.ID, self.user_input_str)
    
    def get_password_input(self):
        return self.driver.find_element(By.ID, self.password_input_str)
    
    def get_checkbox(self):
        return self.driver.find_element(By.ID, self.checkbox_str)
    
    def get_forgot_password(self):
        return self.driver.find_element(By.PARTIAL_LINK_TEXT, self.forgot_password_str)
    
    def get_login_button(self):
        return self.driver.find_element(By.XPATH, self.login_button_str)
    
    def get_back_button(self):
        return self.driver.find_element(By.CLASS_NAME, self.back_button_str)