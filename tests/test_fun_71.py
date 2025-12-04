# test_login_usuarios_inexistentes.py

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from webdriver_manager.chrome import ChromeDriverManager
import time

# Mensaje exacto que muestra el sistema
MENSAJE_ESPERADO = "Estas credenciales no coinciden con nuestros registros."


class LoginPage:
    URL = "https://reportfia.deras.dev/iniciar-sesion"

    def __init__(self, driver):
        self.driver = driver

    # -------- Elementos --------
    def abrir(self):
        self.driver.get(self.URL)

    def input_carnet(self):
        return self.driver.find_element(By.ID, "carnet")

    def input_password(self):
        return self.driver.find_element(By.ID, "password")

    def btn_iniciar_sesion(self):
        return self.driver.find_element(
            By.CSS_SELECTOR,
            "form#loginForm button[type='submit']"
        )

    # -------- Acciones --------
    def iniciar_sesion(self, usuario, contrasena):
        carnet = self.input_carnet()
        password = self.input_password()

        carnet.clear()
        carnet.send_keys(usuario)

        password.clear()
        password.send_keys(contrasena)

        self.btn_iniciar_sesion().click()

    def obtener_mensaje_error(self, timeout=10):
        """
        Obtiene el último mensaje de error de Notyf (.notyf__message).
        Devuelve cadena vacía si no aparece.
        """
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, ".notyf__message"))
            )
            elementos = self.driver.find_elements(By.CSS_SELECTOR, ".notyf__message")
            if not elementos:
                return ""
            # Tomamos el último mensaje mostrado
            return elementos[-1].text.strip()
        except TimeoutException:
            return ""


def test_login_con_tres_usuarios_y_10_intentos_ultimo():
    # Configuración del navegador
    chrome_options = Options()
    # Descomenta la siguiente línea si quieres que corra en modo headless
    # chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--start-maximized")

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=chrome_options
    )

    try:
        login_page = LoginPage(driver)

        # Definimos 3 usuarios inexistentes
        usuarios = [
            ("usuario_no_registrado_1", "pass_invalida_1"),
            ("usuario_no_registrado_2", "pass_invalida_2"),
            ("usuario_no_registrado_3", "pass_invalida_3"),  # A este se le harán 10 intentos
        ]

        for indice, (usuario, contrasena) in enumerate(usuarios, start=1):
            # Para los dos primeros usuarios: 1 intento
            # Para el tercer usuario: 10 intentos
            intentos = 1 if indice < 3 else 10

            print(f"\n=== Probando usuario {indice}: {usuario} | intentos: {intentos} ===")

            # Abrimos la pantalla de login antes de empezar con ese usuario
            login_page.abrir()

            for intento in range(1, intentos + 1):
                print(f" -> Intento {intento} con usuario: {usuario}")

                login_page.iniciar_sesion(usuario, contrasena)

                # Pequeña espera para que el servidor responda y aparezca el toast
                time.sleep(1)

                # Validar que seguimos en la URL de login (no accedió al sistema)
                assert "iniciar-sesion" in driver.current_url, (
                    f"Después del intento {intento} con el usuario '{usuario}' "
                    "NO debería permitir el acceso con credenciales inexistentes."
                )

                # Capturar y validar mensaje de error
                mensaje_error = login_page.obtener_mensaje_error()
                print(f"    Mensaje de error capturado: '{mensaje_error}'")

                assert mensaje_error != "", (
                    f"No se mostró mensaje de error en el intento {intento} "
                    f"para el usuario '{usuario}'."
                )

                assert mensaje_error == MENSAJE_ESPERADO, (
                    f"El mensaje de error no coincide en el intento {intento} "
                    f"para el usuario '{usuario}'.\n"
                    f"Esperado: '{MENSAJE_ESPERADO}'\n"
                    f"Obtenido: '{mensaje_error}'"
                )

        print("\n✅ Prueba completada:")
        print("   - 2 usuarios inexistentes con 1 intento cada uno.")
        print("   - 1 usuario inexistente con 10 intentos.")
        print("   En todos los casos se mostró el mensaje de error esperado y no se permitió el acceso.")

    finally:
        driver.quit()


if __name__ == "__main__":
    test_login_con_tres_usuarios_y_10_intentos_ultimo()
