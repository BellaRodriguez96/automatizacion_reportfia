# tests/tests/tests/test_fun_43.py
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

DEFAULT_WAIT = 15

# Selectores
SELECTORS = {
    "username": (By.ID, "carnet"),
    "password": (By.ID, "password"),
    "submit": (By.CSS_SELECTOR, "button[type='submit']"),
    # "menu_reportes": (By.CSS_SELECTOR, "button[data-collapse-toggle='reportes-dropdown']"),
    # "mis_asignaciones": (By.XPATH, "//a[contains(., 'MIS ASIGNACIONES')]"),
    # "acciones_btn": (By.XPATH, "//button[contains(@aria-label,'acciones') or contains(., 'Acciones') or contains(., '⋮')]"),
    # "cambiar_estado_option": (By.XPATH, "//*[contains(., 'Cambiar estado')]"),
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
        except:
            pass
        time.sleep(1)

    return codigo

def guardar_screenshot(driver, name="fun_43_failure.png"):
    try:
        driver.save_screenshot(name)
        print(f"[INFO] Screenshot guardado: {name}")
    except:
        pass

def verificar_error_500(driver):
    textos_error = [
        "500 Internal Server Error",
        "Ha ocurrido un error inesperado",
        "Por favor vuelve a intentarlo mas tarde"
    ]

    body = driver.find_element(By.TAG_NAME, "body").text.lower()
    for t in textos_error:
        if t.lower() in body:
            guardar_screenshot(driver, "error_500.png")
            pytest.fail(f"Se detectó pantalla 500: {t}")

# ---------------- Fixture -----------------
@pytest.fixture(scope="function")
def driver_setup(request):
    driver = make_chrome_driver(use_profile=False, reset_profile=False)
    yield driver
    driver.quit()

# ---------------- TEST --------------------
@pytest.mark.usefixtures("driver_setup")
def test_fun_43_listado_fondos_se_muestra(driver_setup):
    driver = driver_setup
    wait = WebDriverWait(driver, DEFAULT_WAIT)

    try:
        driver.get(BASE_URL)
        wait.until(EC.visibility_of_element_located(SELECTORS["username"])).send_keys(USERNAME)
        wait.until(EC.visibility_of_element_located(SELECTORS["password"])).send_keys(PASSWORD)
        wait.until(EC.element_to_be_clickable(SELECTORS["submit"])).click()

        time.sleep(1)

        # Si cayó a 2FA
        if "two-factor" in driver.current_url:
            main_tab = driver.current_window_handle

            try:
                driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
            except:
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

            WebDriverWait(driver, DEFAULT_WAIT).until(
                EC.url_contains(URL_INICIO)
            )

        # Ya dentro → ir a mantenimientos
        try:
            wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[data-collapse-toggle="mantenimientos-dropdown"]'))).click()

        except:
            pass

        wait.until(EC.element_to_be_clickable((
            By.CSS_SELECTOR,
            "a[href='/mantenimientos/tipos-incidencias'], a[href='https://reportfia.deras.dev/mantenimientos/tipos-incidencias']"))).click()

        # Esperar que cargue la tabla de fondos
        time.sleep(1.2)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "table")))



        assert True

    except Exception:
        guardar_screenshot(driver)
        pytest.fail(f"Error inesperado en el test:\n{traceback.format_exc()}")
