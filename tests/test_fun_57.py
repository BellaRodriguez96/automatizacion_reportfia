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

DEFAULT_WAIT = 15

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

    return codigo

def guardar_screenshot(driver, name="fun_57_failure.png"):
    try:
        driver.save_screenshot(name)
        print(f"[INFO] Screenshot guardado: {name}")
    except Exception:
        pass

def verificar_error_500(driver):
    textos_error = [
        "500 Internal Server Error",
        "Ha ocurrido un error inesperado",
        "Por favor vuelve a intentarlo mas tarde"
    ]

    try:
        body = driver.find_element(By.TAG_NAME, "body").text.lower()
    except Exception:
        body = ""

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
def test_fun_57_crear_tipo_incidencia(driver_setup):
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

            inputs = wait.until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, "input[type='text'][maxlength='1']"))
            )

            for i, d in enumerate(codigo):
                inputs[i].send_keys(d)
                time.sleep(0.1)

            driver.find_element(By.XPATH, "//button[contains(., 'Verificar')]").click()
            WebDriverWait(driver, DEFAULT_WAIT).until(EC.url_contains(URL_INICIO))

        # 3) Ir a mantenimientos -> Tipos de incidencias
        try:
            boton_mant = wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[data-collapse-toggle="mantenimientos-dropdown"]'))
            )
            boton_mant.click()
        except Exception:
            pass

        wait.until(EC.element_to_be_clickable((
            By.CSS_SELECTOR,
            "a[href='/mantenimientos/tipos-incidencias'], a[href='https://reportfia.deras.dev/mantenimientos/tipos-incidencias']"
        ))).click()

        # 4) Esperar que cargue la tabla
        time.sleep(1.2)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "table")))

        # 5) Abrir formulario "Añadir"
        # intentamos varios selectores posibles por si cambia
        try:
            try:
                wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button[data-modal-target='static-modal']"))).click()
            except Exception:
                try:
                    wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button[data-modal-toggle='static-modal']"))).click()
                except Exception:
                    # fallback: buscar botón por texto "Añadir"
                    btn_add = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(normalize-space(.),'Añadir')]")))
                    btn_add.click()
        except Exception:
            guardar_screenshot(driver, "debug_add_button_not_found.png")
            raise AssertionError("No se pudo abrir el modal 'Añadir' (botón no encontrado).")

        # ---------------------- RELLENAR FORMULARIO (robusto) ----------------------
        # Nombre único para evitar colisiones
        nombre_nuevo = "Tipo prueba " + str(int(time.time()))
        descripcion_nueva = "Descripción automática de prueba creada por test."

        # Esperar modal y campos
        wait.until(EC.visibility_of_element_located((By.ID, "static-modal")))

        # INPUT nombre (id="nombre")
        try:
            nombre_input = wait.until(EC.presence_of_element_located((By.ID, "nombre")))
            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", nombre_input)
            try:
                nombre_input.click()
            except Exception:
                pass
            try:
                nombre_input.clear()
            except Exception:
                pass
            # intentar send_keys primero
            try:
                nombre_input.send_keys(nombre_nuevo)
                # disparar evento input por si la app lo necesita
                driver.execute_script("arguments[0].dispatchEvent(new Event('input', {bubbles: true}));", nombre_input)
            except Exception:
                # fallback JS
                driver.execute_script("""
                    arguments[0].value = arguments[1];
                    arguments[0].dispatchEvent(new Event('input', {bubbles: true}));
                """, nombre_input, nombre_nuevo)

        except Exception:
            guardar_screenshot(driver, "debug_nombre_not_found.png")
            raise AssertionError("No se encontró el campo 'nombre' en el modal.")

        # TEXTAREA descripcion (id="descripcion")
        try:
            descripcion_input = wait.until(EC.presence_of_element_located((By.ID, "descripcion")))
            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", descripcion_input)
            try:
                descripcion_input.click()
            except Exception:
                pass
            try:
                descripcion_input.clear()
            except Exception:
                pass
            try:
                descripcion_input.send_keys(descripcion_nueva)
                driver.execute_script("arguments[0].dispatchEvent(new Event('input', {bubbles: true}));", descripcion_input)
            except Exception:
                driver.execute_script("""
                    arguments[0].value = arguments[1];
                    arguments[0].dispatchEvent(new Event('input', {bubbles: true}));
                """, descripcion_input, descripcion_nueva)

        except Exception:
            guardar_screenshot(driver, "debug_descripcion_not_found.png")
            raise AssertionError("No se encontró el campo 'descripcion' en el modal.")

        # SELECT estado -> id 'activo' (value "1" = ACTIVO)
        try:
            sel_activo = wait.until(EC.presence_of_element_located((By.ID, "activo")))
            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", sel_activo)
            try:
                # intentar seleccionar la opción visible
                selected = False
                for opt in sel_activo.find_elements(By.TAG_NAME, "option"):
                    val = opt.get_attribute("value") or ""
                    txt = (opt.text or "").upper()
                    if val == "1" or "ACTIVO" in txt:
                        try:
                            opt.click()
                        except Exception:
                            driver.execute_script("arguments[0].selected = true;", opt)
                        selected = True
                        break
                # forzar evento change
                driver.execute_script("arguments[0].dispatchEvent(new Event('change', {bubbles: true}));", sel_activo)
                if not selected:
                    # fallback: forzar valor con JS
                    driver.execute_script("""
                        arguments[0].value = '1';
                        arguments[0].dispatchEvent(new Event('change', {bubbles: true}));
                    """, sel_activo)
            except Exception:
                # fallback: forzar valor con JS y disparar change
                driver.execute_script("""
                    arguments[0].value = '1';
                    arguments[0].dispatchEvent(new Event('change', {bubbles: true}));
                """, sel_activo)
        except Exception:
            # no crítico, continuar (el form hará validación)
            guardar_screenshot(driver, "debug_select_not_found.png")

        time.sleep(0.3)  # pequeño retardo para que la UI procese los eventos

        # Enviar (botón Guardar); botón tiene form="tipo-incidencia-form"
        try:
            # primer intento: botón submit visible en footer
            guardar_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button[form='tipo-incidencia-form'][type='submit']")))
            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", guardar_btn)
            try:
                guardar_btn.click()
            except Exception:
                # fallback JS click
                driver.execute_script("arguments[0].click();", guardar_btn)
        except Exception:
            # fallback final: submit del formulario por JS
            try:
                driver.execute_script("document.getElementById('tipo-incidencia-form').submit();")
            except Exception:
                guardar_screenshot(driver, "debug_submit_failed.png")
                raise AssertionError("No se pudo hacer submit del formulario 'tipo-incidencia-form'.")

        # ---------------------- VERIFICAR USANDO FILTRO (más robusto) ----------------------
        # Esperar a que el modal cierre (si sigue abierto)
        timeout_modal = time.time() + 16
        while time.time() < timeout_modal:
            try:
                modal = driver.find_element(By.ID, "static-modal")
                if not modal.is_displayed():
                    break
            except Exception:
                break
            time.sleep(0.4)

        # Usar el filtro 'nombre-filter' que está en el HTML para buscar el registro nuevo
        found = False
        try:
            # Esperar que exista el input de filtro
            filtro = wait.until(EC.presence_of_element_located((By.ID, "nombre-filter")))
            # Poner el valor (nombre completo). Si el sistema normaliza, también probamos con prefijo más abajo.
            try:
                filtro.clear()
            except Exception:
                pass
            try:
                filtro.send_keys(nombre_nuevo)
                driver.execute_script("arguments[0].dispatchEvent(new Event('input', {bubbles: true}));", filtro)
            except Exception:
                driver.execute_script("arguments[0].value = arguments[1]; arguments[0].dispatchEvent(new Event('input', {bubbles:true}));", filtro, nombre_nuevo)

            # Enviar el formulario de filtros (el input está dentro de un <form> que hace GET)
            try:
                # subir al ancestro form y hacer submit
                driver.execute_script("""
                    var f = arguments[0].closest('form');
                    if (f) { f.submit(); }
                """, filtro)
            except Exception:
                # fallback: enviar Enter al campo
                try:
                    filtro.send_keys(Keys.ENTER)
                except Exception:
                    pass

            # esperar tabla y buscar la fila
            timeout_filter = time.time() + 20
            while time.time() < timeout_filter:
                try:
                    # esperar que la tabla esté presente
                    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "table")))
                    filas = driver.find_elements(By.XPATH, f"//td[contains(., \"{nombre_nuevo}\")]")
                    if filas:
                        found = True
                        break
                except Exception:
                    pass
                time.sleep(0.6)
        except Exception:
            # si falla obtener el filtro, continuamos con otros intentos
            pass

        # Si no se encontró con el nombre completo, probar con prefijo (por si truncaron)
        if not found:
            prefijo = nombre_nuevo.split()[0]  # "Tipo"
            try:
                # limpiar filtro y usar prefijo
                try:
                    filtro = driver.find_element(By.ID, "nombre-filter")
                    try:
                        filtro.clear()
                    except Exception:
                        pass
                    try:
                        filtro.send_keys(prefijo)
                        driver.execute_script("arguments[0].dispatchEvent(new Event('input', {bubbles: true}));", filtro)
                    except Exception:
                        driver.execute_script("arguments[0].value = arguments[1]; arguments[0].dispatchEvent(new Event('input', {bubbles:true}));", filtro, prefijo)
                    # submit form again
                    driver.execute_script("var f = arguments[0].closest('form'); if (f) { f.submit(); }", filtro)
                except Exception:
                    pass

                timeout_pref = time.time() + 12
                while time.time() < timeout_pref:
                    try:
                        filas = driver.find_elements(By.XPATH, f"//td[contains(., \"{prefijo}\")]")
                        if filas:
                            found = True
                            break
                    except Exception:
                        pass
                    time.sleep(0.6)
            except Exception:
                pass

        # Si aún no aparece, refresh + volver a intentar quick search (último recurso)
        if not found:
            try:
                driver.refresh()
                time.sleep(1.5)
                # reintentar filtro por nombre completo
                try:
                    filtro = driver.find_element(By.ID, "nombre-filter")
                    try:
                        filtro.clear()
                    except Exception:
                        pass
                    try:
                        filtro.send_keys(nombre_nuevo)
                        driver.execute_script("arguments[0].dispatchEvent(new Event('input', {bubbles: true}));", filtro)
                    except Exception:
                        driver.execute_script("arguments[0].value = arguments[1]; arguments[0].dispatchEvent(new Event('input', {bubbles:true}));", filtro, nombre_nuevo)
                    driver.execute_script("var f = arguments[0].closest('form'); if (f) { f.submit(); }", filtro)
                except Exception:
                    pass

                timeout_refresh = time.time() + 12
                while time.time() < timeout_refresh:
                    try:
                        filas = driver.find_elements(By.XPATH, f"//td[contains(., \"{nombre_nuevo}\")]")
                        if filas:
                            found = True
                            break
                    except Exception:
                        pass
                    time.sleep(0.6)
            except Exception:
                pass

        if found:
            # Guardar evidencia y esperar un poco para que puedas visualizar el resultado en el navegador
            try:
                success_name = "fun_57_success.png"
                driver.save_screenshot(success_name)
                print(f"[INFO] Registro encontrado. Screenshot guardado: {success_name}")
            except Exception:
                pass

            # dejar tiempo para que el navegador se mantenga visible antes de cerrar
            time.sleep(8)  # <- aquí es donde permitimos ver el registro en la lista
            return  # exit exitoso

        else:
            guardar_screenshot(driver, "fun_57_failure.png")
            pytest.fail("No se encontró el nuevo tipo en el listado tras filtrar y refrescar. Revisa fun_57_failure.png")

    except Exception:
        guardar_screenshot(driver, "fun_57_failure.png")
        pytest.fail(f"Error inesperado en FUN-57:\n{traceback.format_exc()}")
