# -*- coding: utf-8 -*-
from time import sleep
from datetime import datetime
import os

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

# ========= CONFIG =========
LOGIN_URL    = "https://reportfia.deras.dev/iniciar-sesion"
FONDOS_URL   = "https://reportfia.deras.dev/mantenimientos/fondos"

CRED_USUARIO = "AA11001"
CRED_PASS    = "pass123"

# Carpeta donde se guarda el perfil de Chrome (cookies, “dispositivo de confianza”, etc.)
CHROME_PROFILE_DIR = os.path.abspath("./chrome-profile-reportfia")
# =========================

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

def new_driver():
    """Chrome con perfil PERSISTENTE (mismo 'dispositivo' entre corridas)."""
    log(f"Creando Chrome con perfil persistente en: {CHROME_PROFILE_DIR}")
    opts = webdriver.ChromeOptions()
    opts.add_argument("--start-maximized")
    opts.page_load_strategy = "normal"
    opts.add_argument(f"--user-data-dir={CHROME_PROFILE_DIR}")  # ⚠️ clave para recordar el dispositivo
    # opts.add_argument("--headless=new")  # si quieres sin ventana
    return webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=opts)

def wait_loader(driver, timeout=15):
    try:
        WebDriverWait(driver, timeout).until(
            EC.any_of(
                EC.invisibility_of_element_located((By.ID, "loader")),
                EC.visibility_of_any_elements_located((By.TAG_NAME, "body"))
            )
        )
    except Exception:
        pass

def is_logged_in(driver, timeout=8):
    try:
        WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located(
                (By.XPATH, "//nav[contains(@class,'fixed') and contains(@class,'z-50')]")
            )
        )
        return True
    except TimeoutException:
        return False

def screenshot(driver, name="debug"):
    ruta = os.path.abspath(f"./{name}_{datetime.now().strftime('%H%M%S')}.png")
    try:
        driver.save_screenshot(ruta)
        log(f"📸 Screenshot: {ruta}")
    except Exception:
        pass

def manejar_2fa(driver):
    """
    Maneja TODO el 2FA:
      1. Clic en 'Enviar código' si aparece.
      2. Si NO aparece ni pantalla de 2FA -> asumimos que no se requiere (dispositivo ya confiable).
      3. Si aparece 'Doble factor de autenticación':
         - Leer código desde consola.
         - Rellenar cajitas.
         - Clic en 'Verificar'.
    En futuras corridas, si el servidor ya confía en el dispositivo, no saldrá esta pantalla.
    """
    log("Revisando flujo de 2FA…")

    # 1) Clic en "Enviar código" si aparece
    try:
        btn_enviar = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable(
                (By.XPATH, "//button[contains(normalize-space(),'Enviar código')]")
            )
        )
        log("Clic en 'Enviar código'…")
        btn_enviar.click()
        wait_loader(driver)
    except TimeoutException:
        log("No se encontró 'Enviar código'. Puede que ya se haya enviado o que no haya 2FA.")

    # 2) Verificar si estamos en "Doble factor de autenticación"
    try:
        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located(
                (By.XPATH, "//h1[contains(normalize-space(),'Doble factor de autenticación')]")
            )
        )
        log("Pantalla de 2FA detectada.")
    except TimeoutException:
        log("No se detectó pantalla de 2FA. Asumimos que NO se requiere (dispositivo ya confiable).")
        return

    # 3) Formulario de confirmar código (no el de reenviar)
    try:
        form_2fa = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located(
                (By.XPATH, "//form[@id='otp-form' and contains(@action,'two-factor/confirmar')]")
            )
        )
    except TimeoutException:
        screenshot(driver, "sin_form_2fa")
        raise TimeoutException("No se encontró el formulario de confirmación de 2FA.")

    inputs = form_2fa.find_elements(By.CSS_SELECTOR, "input[type='text']")
    if not inputs:
        screenshot(driver, "sin_inputs_2fa")
        raise TimeoutException("No se encontraron las cajitas de dígitos del 2FA.")

    n = len(inputs)
    log(f"Se encontraron {n} casillas de código.")

    # 4) Pedir código en consola
    while True:
        otp_raw = input(f"Ingrese el código de verificación de {n} dígitos: ").strip()
        otp = "".join(ch for ch in otp_raw if ch.isdigit())
        if len(otp) == n:
            break
        print(f"El código debe tener exactamente {n} dígitos numéricos. Intente de nuevo.")

    log(f"Código 2FA ingresado: {otp}")

    # 5) Rellenar las cajitas
    for inp, d in zip(inputs, otp):
        inp.clear()
        inp.send_keys(d)

    # 6) Clic en "Verificar"
    try:
        btn_verificar = form_2fa.find_element(
            By.XPATH, ".//button[@type='submit' and contains(normalize-space(),'Verificar')]"
        )
        log("Clic en 'Verificar'…")
        btn_verificar.click()
    except Exception:
        screenshot(driver, "sin_boton_verificar_2fa")
        raise TimeoutException("No se encontró el botón 'Verificar' en el formulario 2FA.")

    wait_loader(driver)

    if not is_logged_in(driver):
        screenshot(driver, "no_navbar_despues_2fa")
        raise TimeoutException("Tras 2FA no se detectó el navbar.")

    log("✅ 2FA completado y sesión iniciada.")

def iniciar_sesion(driver, usuario, password):
    log("Abriendo página de login…")
    driver.get(LOGIN_URL)
    wait_loader(driver)

    # Si ya está logueado por sesión previa, no reingresamos credenciales
    if is_logged_in(driver, timeout=3):
        log("Ya se detecta sesión iniciada (navbar presente). No se reingresan credenciales.")
        return

    # Campos de login
    try:
        carnet = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.ID, "carnet"))
        )
        clave = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.ID, "password"))
        )
    except TimeoutException:
        screenshot(driver, "sin_campos_login")
        raise TimeoutException("No se encontraron campos de login.")

    carnet.clear(); carnet.send_keys(usuario)
    clave.clear();  clave.send_keys(password)

    # Recordarme (si existe)
    try:
        remember = driver.find_element(By.ID, "remember_me")
        if not remember.is_selected():
            remember.click()
    except Exception:
        pass

    # Botón "Iniciar sesión"
    try:
        btn_login = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable(
                (By.XPATH, "//button[normalize-space()='Iniciar sesión' and @type='submit']")
            )
        )
        log("Clic en 'Iniciar sesión'…")
        btn_login.click()
    except TimeoutException:
        screenshot(driver, "sin_boton_login")
        raise TimeoutException("No se encontró el botón 'Iniciar sesión'.")

    wait_loader(driver)

    # 2FA si aplica (primera(s) vez/veces)
    manejar_2fa(driver)

    # Validar navbar (logueado)
    if not is_logged_in(driver):
        screenshot(driver, "no_navbar_final")
        raise TimeoutException("No se detectó navbar tras el login.")

    log("✅ Sesión iniciada correctamente.")


# ========= CASO DE PRUEBA: CREAR FONDO =========

def generar_nombre_fondo_unico():
    """
    Genera un nombre único para el fondo.
    El patrón del campo permite letras, números, puntos y espacios (hasta 100 chars).
    """
    return "FONDO SELENIUM " + datetime.now().strftime("%Y%m%d%H%M%S")

def crear_fondo(driver):
    """
    Caso de prueba:
      1. Ir a /mantenimientos/fondos
      2. Clic en botón 'Añadir' (abre modal)
      3. Llenar formulario (nombre, descripción, estado)
      4. Guardar
      5. Verificar que el fondo aparece en la tabla
    """
    wait_loader(driver)

    log("Navegando a pantalla Gestión de Fondos…")
    driver.get(FONDOS_URL)
    wait_loader(driver)

    # Validar que cargó la pantalla
    try:
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located(
                (By.XPATH, "//div[contains(@class,'font-bold') and contains(normalize-space(),'Gestión de Fondos')]")
            )
        )
    except TimeoutException:
        screenshot(driver, "no_gestion_fondos")
        raise TimeoutException("No se detectó la pantalla 'Gestión de Fondos'.")

    # Botón "Añadir" que abre el modal
    try:
        btn_anadir = WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable(
                (By.XPATH, "//button[@data-modal-target='static-modal' and contains(normalize-space(),'Añadir')]")
            )
        )
        log("Clic en botón 'Añadir'…")
        btn_anadir.click()
    except TimeoutException:
        screenshot(driver, "sin_boton_anadir_fondo")
        raise TimeoutException("No se encontró el botón 'Añadir' en Gestión de Fondos.")

    # Esperar que el modal esté visible
    try:
        modal = WebDriverWait(driver, 15).until(
            EC.visibility_of_element_located((By.ID, "static-modal"))
        )
    except TimeoutException:
        screenshot(driver, "modal_fondos_no_visible")
        raise TimeoutException("El modal de Fondos no se mostró correctamente.")

    # Campos dentro del modal
    try:
        campo_nombre = WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable((By.ID, "nombre"))
        )
        campo_descripcion = modal.find_element(By.ID, "descripcion")
        select_estado = modal.find_element(By.ID, "activo")
    except Exception:
        screenshot(driver, "campos_modal_fondos_incompletos")
        raise TimeoutException("No se encontraron los campos del modal de Fondos.")

    # Datos a ingresar
    nombre_fondo = generar_nombre_fondo_unico()
    descripcion_fondo = "Fondo creado automáticamente por prueba con Selenium."

    campo_nombre.clear()
    campo_nombre.send_keys(nombre_fondo)

    campo_descripcion.clear()
    campo_descripcion.send_keys(descripcion_fondo)

    # Estado ACTIVO (value="1")
    Select(select_estado).select_by_value("1")

    log(f"Llenando modal con nombre de fondo: {nombre_fondo}")

    # Botón "Guardar"
    try:
        btn_guardar = modal.find_element(
            By.XPATH, ".//button[@type='submit' and @form='fondo-form']"
        )
        log("Clic en 'Guardar' del modal de Fondos…")
        btn_guardar.click()
    except Exception:
        screenshot(driver, "sin_boton_guardar_fondo")
        raise TimeoutException("No se encontró el botón 'Guardar' en el modal de Fondos.")

    wait_loader(driver)

    # Esperar que el modal desaparezca
    try:
        WebDriverWait(driver, 15).until(
            EC.invisibility_of_element_located((By.ID, "static-modal"))
        )
    except TimeoutException:
        log("⚠️ El modal de Fondos tardó o no se ocultó claramente, se continúa de todos modos.")

    # Verificar en la tabla que el fondo existe
    log("Verificando que el nuevo fondo aparezca en la tabla…")
    driver.get(FONDOS_URL)
    wait_loader(driver)

    try:
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located(
                (By.XPATH, f"//table//tbody//tr//td/div[normalize-space()='{nombre_fondo}']")
            )
        )
        log(f"✅ Fondo creado y visible en la tabla: {nombre_fondo}")
    except TimeoutException:
        screenshot(driver, "fondo_no_encontrado_en_tabla")
        raise TimeoutException(f"No se encontró en la tabla el fondo recién creado: {nombre_fondo}")


# ================= MAIN =================

if __name__ == "__main__":
    driver = new_driver()
    try:
        # 1) Login con persistencia (tu lógica)
        iniciar_sesion(driver, CRED_USUARIO, CRED_PASS)
        log("🔵 Sesión lista. Iniciando caso de prueba: creación de fondo.")

        # 2) Caso de prueba: crear fondo
        crear_fondo(driver)

        log("🔵 Caso de prueba finalizado. Revisa la tabla de Fondos en ReportFIA.")
        sleep(5)
    except Exception as e:
        log(f"❌ Error en el flujo: {e}")
        screenshot(driver, "error_general")
        raise
    finally:
        driver.quit()
