# tests/test_fun_57.py
import os
import time
import re
import shutil
import traceback

import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# ================= CONFIG =================
BASE_URL = "https://reportfia.deras.dev/iniciar-sesion"
USERNAME = "aa11001"
PASSWORD = "pass123"
YOPMAIL_URL = "https://yopmail.com/es/"
URL_INICIO = "https://reportfia.deras.dev/inicio"

CHROME_PROFILE_DIR = os.path.abspath("./.chrome-profile-reportfia")
CHROME_SUBPROFILE = "ReportFIAProfile"

DEFAULT_WAIT = 5

# Pausas / timeouts que puedes ajustar
FIND_TIMEOUT = 5            # tiempo máximo para buscar la fila filtrada
VISIBILITY_PAUSE = 5        # segundos que deja visible la fila para inspección manual

# Selectores (mínimos usados en este test)
SELECTORS = {
    "username": (By.ID, "carnet"),
    "password": (By.ID, "password"),
    "submit": (By.CSS_SELECTOR, "button[type='submit']"),
}

# ---------------- Helpers -----------------
def limpiar_perfil_chrome():
    if os.path.exists(CHROME_PROFILE_DIR):
        shutil.rmtree(CHROME_PROFILE_DIR, ignore_errors=True)

def make_chrome_driver(use_profile=False, reset_profile=False):
    if use_profile and reset_profile:
        limpiar_perfil_chrome()

    options = webdriver.ChromeOptions()
    if use_profile:
        options.add_argument(f"--user-data-dir={CHROME_PROFILE_DIR}")
        options.add_argument(f"--profile-directory={CHROME_SUBPROFILE}")

    options.add_argument("--start-maximized")
    options.page_load_strategy = "normal"

    return webdriver.Chrome(
        service=ChromeService(ChromeDriverManager().install()),
        options=options
    )

def abrir_yopmail_y_obtener_codigo(driver, wait, inbox_name, timeout=20):
    """
    Abre yopmail en una nueva pestaña, ingresa el inbox_name y busca
    un código numérico de 6 dígitos dentro del iframe 'ifmail'.
    """
    driver.switch_to.window(driver.window_handles[0])
    driver.execute_script("window.open('about:blank', '_blank');")
    time.sleep(0.3)
    driver.switch_to.window(driver.window_handles[-1])
    driver.get(YOPMAIL_URL)

    campo = wait.until(EC.presence_of_element_located((By.ID, "login")))
    campo.clear()
    campo.send_keys(inbox_name)
    campo.send_keys(Keys.ENTER)
    time.sleep(1)

    # Buscar iframe donde está el correo
    for f in driver.find_elements(By.TAG_NAME, "iframe"):
        name = f.get_attribute("name") or ""
        if "ifmail" in name:
            driver.switch_to.frame(f)
            break

    time_limit = time.time() + timeout
    codigo = None

    while time.time() < time_limit:
        try:
            text = driver.find_element(By.TAG_NAME, "body").text
            m = re.search(r"\b\d{6}\b", text)
            if m:
                codigo = m.group(0)
                break
        except Exception:
            pass
        time.sleep(1)

    # cerrar pestaña yopmail y volver a la principal
    try:
        driver.close()
        driver.switch_to.window(driver.window_handles[0])
    except Exception:
        pass

    return codigo

def guardar_screenshot(driver, name="fun_57_failure.png"):
    try:
        driver.save_screenshot(name)
        print(f"[INFO] Screenshot guardado: {name}")
    except Exception:
        pass

def esperar_fila(driver, texto_a_buscar, timeout=FIND_TIMEOUT):
    """
    Busca una celda <td> que contenga el texto dado dentro de la tabla.
    Devuelve True si se encuentra dentro del timeout, False en caso contrario.
    """
    end_time = time.time() + timeout
    while time.time() < end_time:
        try:
            elementos = driver.find_elements(By.XPATH, f"//td[contains(normalize-space(.), \"{texto_a_buscar}\")]")
            if elementos:
                try:
                    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", elementos[0])
                except Exception:
                    pass
                return True
        except Exception:
            pass
        time.sleep(0.5)
    return False

def click_aplicar_filtros(driver, wait):
    """
    Hace click en el botón de buscar/aplicar filtros (el botón 'submit' del formulario).
    Si no lo encuentra, intenta hacer submit del formulario por JS.
    """
    try:
        btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button[data-tooltip-target='tooltip-aplicar-filtros'], form button[type='submit']")))
        try:
            btn.click()
        except Exception:
            driver.execute_script("arguments[0].click();", btn)
        return
    except Exception:
        # fallback: submit del formulario por JS (si el formulario tiene action y id no conocido)
        try:
            driver.execute_script("""
                var f = document.querySelector('form[action*="/mantenimientos/bienes"]');
                if (f) { f.submit(); }
            """)
            return
        except Exception:
            raise

def resetear_filtros(driver, wait):
    """
    Usa el botón de reset (que en el HTML hace window.location.href=...) para volver al listado original.
    """
    try:
        btn_reset = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button[type='reset']")))
        try:
            btn_reset.click()
        except Exception:
            driver.execute_script("arguments[0].click();", btn_reset)
        # esperar que la URL se estabilice (puede recargar)
        time.sleep(1.0)
    except Exception:
        # fallback: navegar directamente a la URL de bienes
        driver.get("https://reportfia.deras.dev/mantenimientos/bienes")
        time.sleep(1.0)

# ---------------- Fixture -----------------
@pytest.fixture(scope="function")
def driver_setup(request):
    driver = make_chrome_driver(use_profile=False, reset_profile=False)
    yield driver
    driver.quit()

# ---------------- TEST --------------------
@pytest.mark.usefixtures("driver_setup")
def test_bienes_filtrar_por_campos(driver_setup):
    """
    Test que comprueba los filtros de la pantalla 'Gestión de bienes':
    1) Filtra por Nombre (ej: 'SILLA RECLINABLE V2')
    2) Filtra por Código (ej: 'S-6011')
    3) Filtra por Estado (ej: 'ACTIVO' -> value=1)
    Mantiene la lógica de 2FA previa si la app la solicita.
    """
    driver = driver_setup
    wait = WebDriverWait(driver, DEFAULT_WAIT)

    try:
        # 1) Login
        driver.get(BASE_URL)
        wait.until(EC.visibility_of_element_located(SELECTORS["username"])).send_keys(USERNAME)
        wait.until(EC.visibility_of_element_located(SELECTORS["password"])).send_keys(PASSWORD)
        wait.until(EC.element_to_be_clickable(SELECTORS["submit"])).click()

        time.sleep(1)

        # 2) 2FA (si aplica) - reutiliza abrir_yopmail_y_obtener_codigo
        if "two-factor" in driver.current_url:
            main_tab = driver.current_window_handle
            try:
                driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
            except Exception:
                pass

            codigo = abrir_yopmail_y_obtener_codigo(driver, wait, USERNAME)
            assert codigo, "No se pudo obtener el código 2FA"

            driver.switch_to.window(main_tab)

            inputs = wait.until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, "input[type='text'][maxlength='1']"))
            )

            for i, d in enumerate(codigo):
                inputs[i].send_keys(d)
                time.sleep(0.1)

            driver.find_element(By.XPATH, "//button[contains(., 'Verificar')]").click()
            WebDriverWait(driver, DEFAULT_WAIT).until(EC.url_contains(URL_INICIO))

        # 3) Ir a mantenimientos -> Bienes
        try:
            boton_mant = wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[data-collapse-toggle="mantenimientos-dropdown"]'))
            )
            boton_mant.click()
        except Exception:
            pass

        wait.until(EC.element_to_be_clickable((
            By.CSS_SELECTOR,
            "a[href='/mantenimientos/bienes'], a[href='https://reportfia.deras.dev/mantenimientos/bienes']"
        ))).click()

        # 4) Esperar que cargue la tabla
        time.sleep(1.2)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "table")))

        # --- FILTRO 1: POR NOMBRE ---
        nombre_ejemplo = "SILLA RECLINABLE V2"   # valor tomado de la lista de ejemplo
        try:
            input_nombre = wait.until(EC.presence_of_element_located((By.ID, "nombre-filter")))
            input_nombre.clear()
            input_nombre.send_keys(nombre_ejemplo)
            # disparar evento input por si la app lo requiere
            driver.execute_script("arguments[0].dispatchEvent(new Event('input', {bubbles:true}));", input_nombre)
        except Exception:
            guardar_screenshot(driver, "fun_59_failure.png")
            pytest.fail("No se encontró el input 'nombre-filter' para aplicar el filtro por nombre.")

        # aplicar filtros (submit)
        click_aplicar_filtros(driver, wait)

        # esperar y validar fila
        found = esperar_fila(driver, nombre_ejemplo, timeout=FIND_TIMEOUT)
        assert found, f"Filtro por NOMBRE falló: no se encontró '{nombre_ejemplo}' en la tabla después de filtrar."
        # dejar visible unos segundos para inspección
        time.sleep(VISIBILITY_PAUSE)

        # resetear filtros antes del siguiente caso
        resetear_filtros(driver, wait)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "table")))
        time.sleep(0.6)

        # --- FILTRO 2: POR CÓDIGO ---
        codigo_ejemplo = "S-6011"   # valor tomado de la lista de ejemplo
        try:
            input_codigo = wait.until(EC.presence_of_element_located((By.ID, "codigo-filter")))
            input_codigo.clear()
            input_codigo.send_keys(codigo_ejemplo)
            driver.execute_script("arguments[0].dispatchEvent(new Event('input', {bubbles:true}));", input_codigo)
        except Exception:
            guardar_screenshot(driver, "fun_57_failure.png")
            pytest.fail("No se encontró el input 'codigo-filter' para aplicar el filtro por código.")

        click_aplicar_filtros(driver, wait)

        found = esperar_fila(driver, codigo_ejemplo, timeout=FIND_TIMEOUT)
        assert found, f"Filtro por CÓDIGO falló: no se encontró '{codigo_ejemplo}' en la tabla después de filtrar."
        time.sleep(VISIBILITY_PAUSE)

        resetear_filtros(driver, wait)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "table")))
        time.sleep(0.6)

        # --- FILTRO 3: POR ESTADO ---
        # El select tiene id 'estado-bien-filter' y los valores: 1=ACTIVO, 2=INACTIVO, 3=DESCARGO
        estado_val = "1"
        estado_texto_ejemplo = "ACTIVO"  # usado para buscar en la celda
        try:
            sel_estado = wait.until(EC.presence_of_element_located((By.ID, "estado-bien-filter")))
            # seleccionar con JS por valor y disparar change
            driver.execute_script("""
                arguments[0].value = arguments[1];
                arguments[0].dispatchEvent(new Event('change', {bubbles: true}));
            """, sel_estado, estado_val)
        except Exception:
            guardar_screenshot(driver, "fun_57_failure.png")
            pytest.fail("No se encontró el select 'estado-bien-filter' para aplicar el filtro por estado.")

        click_aplicar_filtros(driver, wait)

        found = esperar_fila(driver, estado_texto_ejemplo, timeout=FIND_TIMEOUT)
        assert found, f"Filtro por ESTADO ({estado_texto_ejemplo}) falló: no se encontraron filas con estado '{estado_texto_ejemplo}'."
        time.sleep(VISIBILITY_PAUSE)

        # todo OK
    except Exception:
        guardar_screenshot(driver, "fun_57_failure.png")
        pytest.fail(f"Error inesperado en la prueba de filtros:\n{traceback.format_exc()}")
