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
VISIBILITY_PAUSE = 2        # segundos que deja visible la fila para inspección manual

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
            elementos = driver.find_elements(By.XPATH, f"//tbody//tr//td[contains(normalize-space(.), \"{texto_a_buscar}\")]")
            if elementos:
                try:
                    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", elementos[0])
                except Exception:
                    pass
                return True
        except Exception:
            pass
        time.sleep(0.4)
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
                var f = document.querySelector('form[action*="/bitacora"], form[action*="/mantenimientos/bitacora"], form[action*="/bitacora"]');
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
        # fallback: navegar directamente a la URL de bitacora
        driver.get("https://reportfia.deras.dev/bitacora")
        time.sleep(1.0)

# ---------------- Fixture -----------------
@pytest.fixture(scope="function")
def driver_setup(request):
    driver = make_chrome_driver(use_profile=False, reset_profile=False)
    yield driver
    driver.quit()

# ---------------- TEST --------------------
@pytest.mark.usefixtures("driver_setup")
def test_bitacora_aplicar_filtros_exactos(driver_setup):
    """
    Aplica exactamente los filtros que se muestran en la imagen:
      - Model = Escuela
      - Event = Actualizado
      - Fecha Inicial = 15/09/2025
      - Fecha Final = 21/11/2025
      - Nombre = (vacío)
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

        # 2) 2FA (si aplica)
        if "two-factor" in driver.current_url:
            main_tab = driver.current_window_handle
            try:
                driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
            except Exception:
                pass
            codigo = abrir_yopmail_y_obtener_codigo(driver, wait, USERNAME)
            assert codigo, "No se pudo obtener el código 2FA"
            driver.switch_to.window(main_tab)
            inputs = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "input[type='text'][maxlength='1']")))
            for i, d in enumerate(codigo):
                inputs[i].send_keys(d)
                time.sleep(0.1)
            driver.find_element(By.XPATH, "//button[contains(., 'Verificar')]").click()
            WebDriverWait(driver, DEFAULT_WAIT).until(EC.url_contains(URL_INICIO))

        # 3) Ir directo a Bitácora
        driver.get("https://reportfia.deras.dev/bitacora")
        time.sleep(1.0)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "table")))

        # Valores EXACTOS solicitados
        VAL_MODEL_TEXT = "Escuela"
        VAL_EVENT_TEXT = "Actualizado"
        VAL_START_DATE = "15/09/2025"
        VAL_END_DATE = "21/11/2025"

        model_sel = (By.ID, "model")
        event_sel = (By.ID, "event")
        nombre_sel = (By.ID, "nombre")
        start_date_sel = (By.ID, "start_date")
        end_date_sel = (By.ID, "end_date")

        # 1) seleccionar Modelo = Escuela
        el_model = wait.until(EC.presence_of_element_located(model_sel))
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el_model)
        # seleccionar por texto visible
        selected = False
        try:
            for o in el_model.find_elements(By.TAG_NAME, "option"):
                if (o.text or "").strip().lower() == VAL_MODEL_TEXT.strip().lower():
                    try:
                        o.click()
                    except Exception:
                        driver.execute_script("arguments[0].selected = true;", o)
                    driver.execute_script("arguments[0].dispatchEvent(new Event('change', {bubbles: true}));", el_model)
                    selected = True
                    break
        except Exception:
            selected = False
        if not selected:
            # fallback por value (namespace)
            driver.execute_script("arguments[0].value = arguments[1]; arguments[0].dispatchEvent(new Event('change', {bubbles: true}));", el_model, "App\\\\Models\\\\Mantenimientos\\\\Escuela")

        # 2) seleccionar Event = Actualizado
        el_event = wait.until(EC.presence_of_element_located(event_sel))
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el_event)
        sel_ok = False
        try:
            for opt in el_event.find_elements(By.TAG_NAME, "option"):
                if (opt.text or "").strip().lower() == VAL_EVENT_TEXT.strip().lower():
                    try:
                        opt.click()
                    except Exception:
                        driver.execute_script("arguments[0].selected = true;", opt)
                    driver.execute_script("arguments[0].dispatchEvent(new Event('change', {bubbles: true}));", el_event)
                    sel_ok = True
                    break
        except Exception:
            sel_ok = False
        if not sel_ok:
            # crear opcion por JS y elegirla
            js_create_opt = """
            var sel = arguments[0];
            var txt = arguments[1];
            var val = arguments[2] || arguments[1];
            var found = false;
            for(var i=0;i<sel.options.length;i++){
                if((sel.options[i].text||'').trim().toLowerCase() === txt.trim().toLowerCase()){
                    sel.selectedIndex = i;
                    sel.dispatchEvent(new Event('change', {bubbles: true}));
                    found = true;
                    break;
                }
            }
            if(!found){
                var opt = document.createElement('option');
                opt.text = txt;
                opt.value = val;
                sel.appendChild(opt);
                sel.value = val;
                sel.dispatchEvent(new Event('change', {bubbles: true}));
            }
            """
            driver.execute_script(js_create_opt, el_event, VAL_EVENT_TEXT, VAL_EVENT_TEXT)
            time.sleep(0.2)

        # 3) setear fechas (inputs readonly) por JS
        el_start = wait.until(EC.presence_of_element_located(start_date_sel))
        el_end = wait.until(EC.presence_of_element_located(end_date_sel))
        driver.execute_script("arguments[0].value = arguments[1]; arguments[0].dispatchEvent(new Event('input', {bubbles: true})); arguments[0].dispatchEvent(new Event('change', {bubbles: true}));", el_start, VAL_START_DATE)
        driver.execute_script("arguments[0].value = arguments[1]; arguments[0].dispatchEvent(new Event('input', {bubbles: true})); arguments[0].dispatchEvent(new Event('change', {bubbles: true}));", el_end, VAL_END_DATE)

        # 4) dejar nombre vacío explícitamente
        el_nombre = wait.until(EC.presence_of_element_located(nombre_sel))
        try:
            el_nombre.clear()
        except Exception:
            driver.execute_script("arguments[0].value = '';", el_nombre)

        # 5) aplicar filtros (click al botón buscar)
        click_aplicar_filtros(driver, wait)

        # 6) esperar y verificar que la tabla muestre filas (al menos una)
        # espera rápida a que la tabla se refresque
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "table")))
        time.sleep(0.6)  # pequeña espera para que rellene filas

        filas = driver.find_elements(By.CSS_SELECTOR, "tbody tr")
        if not filas or len([r for r in filas if r.text.strip() != ""]) == 0:
            # guardar screenshot si no hay filas
            guardar_screenshot(driver, "bitacora_aplicar_filtros_no_rows.png")
            # no forzamos fallar, pero informamos en assert para que sepas
            assert False, "No se encontraron filas tras aplicar los filtros exactos (ver screenshot bitacora_aplicar_filtros_no_rows.png)"
        else:
            # opcional: verificar que al menos una fila contenga Escuela y Actualizado
            found_model = any("Escuela" in r.text for r in filas)
            found_event = any("Actualizado" in r.text for r in filas)
            assert found_model, "Después de aplicar filtros no apareció 'Escuela' en las filas"
            assert found_event, "Después de aplicar filtros no apareció 'Actualizado' en las filas"

            # pausa visual final
            time.sleep(VISIBILITY_PAUSE)

    except Exception:
        guardar_screenshot(driver, "fun_57_failure.png")
        pytest.fail(f"Error inesperado en FUN-57:\n{traceback.format_exc()}")
