import pytest
from helpers.object_manager import ObjectManager

@pytest.fixture()
def manager():
    """
    Fixture que devuelve el ObjectManager (driver + page objects reutilizables).
    """
    om = ObjectManager()
    yield om
    om.quit()

# Test para login con credenciales inválidas
def test_invalidLogin(manager):
    # Usar manager en lugar de instancias separadas
    base = manager.base
    home_page = manager.home
    login_page = manager.login
    
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

    #Ingresar credenciales de usuario
    base.enter_text(login_page.get_user_input(), "AA11001")
    base.enter_text(login_page.get_password_input(), "prueba123")
    base.clickElement(login_page.get_login_button())