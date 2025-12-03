# tests/test_fun_74.py
# Caso: registro de estudiante con campos vacíos

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
import time, os, traceback

# ================= CONFIG =================
HOME_URL = "https://reportfia.deras.dev"
OUTPUT_DIR = "selenium_outputs_registro_vacio"
os.makedirs(OUTPUT_DIR, exist_ok=True)
TIMEOUT = 12

# Datos que sí se llenan (como en la captura)
TEST_DATA = {
    "nombre": "PRUEBA",
    "apellido": "PRUEBA",
    "fecha_nacimiento": "15/11/1996",
    "escuela_value": "2",
    "telefono": "6666666"
}

# =============== HELPERS ====================
def screenshot(driver, name):
    filename = f"{int(time.time()*1000)}_{name}.png"
    path = os.path.join(OUTPUT_DIR, filename)
    driver.save_screenshot(path)

def found_validation_message(driver):
    """Detecta mensajes de validación por campos vacíos."""
    text = driver.find_element(By.TAG_NAME, "body").get_attribute("innerText").lower()
    keywords = ["por favor", "ingresa", "completa", "obligatorio", "debe", "campo"]
    return any(k in text for k in keywords)

# =============== TEST =======================
def test_registro_campo_vacio():

    driver = webdriver.Chrome(
        service=ChromeService(ChromeDriverManager().install())
    )
    driver.maximize_window()

    try:
        # 1) Home
        driver.get(HOME_URL)
        screenshot(driver, "01_home")

        # 2) Click "Registrarse"
        btn_reg = WebDriverWait(driver, TIMEOUT).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "a[href*='/registrarse']"))
        )
        btn_reg.click()

        WebDriverWait(driver, TIMEOUT).until(
            EC.url_contains("/registrarse")
        )
        screenshot(driver, "02_register_page")

        # 3) Llenar campos de la captura
        WebDriverWait(driver, TIMEOUT).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "form"))
        )

        driver.find_element(By.NAME, "nombre").send_keys(TEST_DATA["nombre"])
        driver.find_element(By.NAME, "apellido").send_keys(TEST_DATA["apellido"])

        # Fecha readonly → se asigna con JS
        js = """
        const el = document.querySelector('input[name="fecha_nacimiento"]');
        el.value = arguments[0];
        el.dispatchEvent(new Event('input', {bubbles:true}));
        el.dispatchEvent(new Event('change', {bubbles:true}));
        """
        driver.execute_script(js, TEST_DATA["fecha_nacimiento"])

        # Escuela
        Select(driver.find_element(By.NAME, "escuela")).select_by_value(TEST_DATA["escuela_value"])

        # Teléfono
        driver.find_element(By.NAME, "telefono").send_keys(TEST_DATA["telefono"])

        # Email, password y confirm → vacíos a propósito
        screenshot(driver, "03_partial_filled")

        # 4) Enviar formulario
        driver.find_element(By.CSS_SELECTOR, "form button[type='submit']").click()
        time.sleep(1.3)
        screenshot(driver, "04_after_submit")

        # 5) Aserción: debe aparecer validación
        assert found_validation_message(driver), \
            "❌ No se mostró mensaje de validación al dejar campos vacíos"

    except Exception:
        screenshot(driver, "error")
        raise

    finally:
        driver.quit()
