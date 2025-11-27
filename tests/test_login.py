import pytest
from pages.base import Base
from pages.home_page import HomePage
from pages.login_page import LoginPage


@pytest.fixture()
def driver():
    """
    Fixture de configuración para inicializar la página base y el driver de Selenium.
    """
    # Crear la instancia Base sin driver, luego obtener el WebDriver
    base_page = Base()
    driver = base_page.get_driver()
    base_page.open_page(driver)
    yield driver
    base_page.quit_driver(driver)

def test_login(driver):
    """
    Test para registrar un nuevo usuario.
    """
    # Asignar el driver a la instancia Base para poder usar sus utilidades
    base = Base(driver)

    # Inicializa la página de inicio y hacer clic en el botón de login/signup
    home_page = HomePage(driver)
    login_page = LoginPage(driver)
    
    # Hacer clic en el botón de login en la página de inicio
    base.clickElement(home_page.get_loginButton())

    # Verificar que todos los elementos de la página de login estén visibles
    base.wait_for(login_page.get_logo(), "visible")
    base.wait_for(login_page.get_user_input(), "visible")
    base.wait_for(login_page.get_password_input(), "visible")
    base.wait_for(login_page.get_checkbox(), "visible")
    base.wait_for(login_page.get_forgot_password(), "visible")
    base.wait_for(login_page.get_login_button(), "visible")
    base.wait_for(login_page.get_back_button(), "visible")