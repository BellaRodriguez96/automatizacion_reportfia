# -*- coding: utf-8 -*-
from time import sleep
from datetime import datetime
import os

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

# ========= CONFIG =========
BASE_URL     = "https://reportfia.deras.dev"
LOGIN_URL    = f"{BASE_URL}/iniciar-sesion"
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
    return webdriver.Chrome(
        service=ChromeService(ChromeDriverManager().install()),
        options=opts
    )

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

# ==============================
#   UNIDADES DE MEDIDA
# ==============================

def ir_a_unidades_medida(driver):
    """
    Navega a la pantalla:
        /mantenimientos/unidades-medida
    y valida que cargó Gestión de Unidades de Medida.
    """
    log("Navegando a Gestión de Unidades de Medida…")
    driver.get(f"{BASE_URL}/mantenimientos/unidades-medida")
    wait_loader(driver)

    try:
        WebDriverWait(driver, 15).until(
            EC.visibility_of_element_located(
                (By.XPATH, "//*[contains(@class,'text-2xl') and contains(normalize-space(),'Gestión de Unidades de Medida')]")
            )
        )
        log("Pantalla de Unidades de Medida cargada correctamente.")
    except TimeoutException:
        screenshot(driver, "unidades_medida_no_carga")
        raise TimeoutException("No se detectó la pantalla de Unidades de Medida.")

def crear_unidad_medida(driver, nombre_unidad, estado="ACTIVO"):
    """
    Crea una unidad de medida en:
        /mantenimientos/unidades-medida

    estado: "ACTIVO" o "INACTIVO"
    """
    ir_a_unidades_medida(driver)

    wait = WebDriverWait(driver, 15)

    # 1) Clic en botón "Añadir" -> abre modal #static-modal
    try:
        boton_aniadir = wait.until(
            EC.element_to_be_clickable(
                (By.CSS_SELECTOR, "button[data-modal-target='static-modal']")
            )
        )
        log("Clic en botón 'Añadir'…")
        boton_aniadir.click()
    except TimeoutException:
        screenshot(driver, "sin_boton_aniadir_unidad")
        raise TimeoutException("No se encontró el botón 'Añadir' en Unidades de Medida.")

    # 2) Esperar que el modal esté visible
    try:
        wait.until(EC.visibility_of_element_located((By.ID, "static-modal")))
    except TimeoutException:
        screenshot(driver, "modal_unidad_no_visible")
        raise TimeoutException("No se mostró el modal de Unidad de Medida.")

    # 3) Llenar campo "Nombre"
    try:
        nombre_input = wait.until(
            EC.visibility_of_element_located((By.ID, "nombre"))
        )
    except TimeoutException:
        screenshot(driver, "sin_campo_nombre_unidad")
        raise TimeoutException("No se encontró el campo 'Nombre' en el modal.")

    nombre_form = nombre_unidad.strip()
    nombre_input.clear()
    nombre_input.send_keys(nombre_form)
    log(f"Nombre de unidad a crear: {nombre_form}")

    # 4) Seleccionar "Estado" en el select id="activo"
    try:
        select_estado = wait.until(
            EC.visibility_of_element_located((By.ID, "activo"))
        )
    except TimeoutException:
        screenshot(driver, "sin_select_estado_unidad")
        raise TimeoutException("No se encontró el select 'Estado' en el modal.")

    # Click y selección según valor
    select_estado.click()
    if estado.upper().startswith("ACT"):
        # value="1" -> ACTIVO
        opcion = driver.find_element(
            By.XPATH, "//select[@id='activo']/option[@value='1']"
        )
        log("Seleccionando estado: ACTIVO")
    else:
        # value="0" -> INACTIVO
        opcion = driver.find_element(
            By.XPATH, "//select[@id='activo']/option[@value='0']"
        )
        log("Seleccionando estado: INACTIVO")
    opcion.click()

    # 5) Clic en botón "Guardar" (form="unidad-form")
    try:
        boton_guardar = driver.find_element(
            By.CSS_SELECTOR,
            "button[form='unidad-form'][type='submit']"
        )
        log("Clic en 'Guardar'…")
        boton_guardar.click()
    except Exception:
        screenshot(driver, "sin_boton_guardar_unidad")
        raise TimeoutException("No se encontró el botón 'Guardar' en el modal de Unidad.")

    wait_loader(driver)

    # 6) Verificar que la unidad aparezca en la tabla
    # En la tabla los nombres salen en mayúsculas.
    nombre_busqueda = nombre_form.upper()
    log(f"Verificando en tabla la unidad: {nombre_busqueda}")

    try:
        fila_nueva = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((
                By.XPATH,
                f"//table//tbody//tr[td//div[normalize-space(text())='{nombre_busqueda}']]"
            ))
        )
        if fila_nueva:
            log(f"✅ Unidad de medida '{nombre_busqueda}' creada y visible en la tabla.")
    except TimeoutException:
        screenshot(driver, "unidad_no_en_tabla")
        raise TimeoutException(
            f"No se encontró la unidad '{nombre_busqueda}' en la tabla después de guardar."
        )

# ==============================
#   MAIN
# ==============================

if __name__ == "__main__":
    driver = new_driver()
    try:
        # 1) Iniciar sesión (con persistencia y 2FA si aplica)
        iniciar_sesion(driver, CRED_USUARIO, CRED_PASS)
        log("🔵 Deberías ver ReportFIA ya autenticado.")

        # 2) Crear una unidad de medida de ejemplo
        #    Cambia "CAJAS" por el nombre que quieras probar
        crear_unidad_medida(driver, "CAJAS", estado="ACTIVO")

        log("🔵 Flujo de creación de Unidad de Medida finalizado.")
        sleep(5)  # pequeña pausa para que puedas ver la tabla antes de cerrar
    except Exception as e:
        log(f"❌ Error en el flujo: {e}")
        screenshot(driver, "error_general")
        raise
    finally:
        driver.quit()
