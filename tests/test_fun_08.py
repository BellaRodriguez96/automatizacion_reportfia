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
LOGIN_URL    = "https://reportfia.deras.dev/iniciar-sesion"
PERFIL_URL   = "https://reportfia.deras.dev/perfil"

CRED_USUARIO = "HG16037"
CRED_PASS    = "PassNueva123*"      # contraseña ACTUAL con la que entras

# Para esta PRUEBA ESPECÍFICA:
# Se intenta actualizar la contraseña usando la MISMA contraseña actual
PASS_ACTUAL = CRED_PASS
PASS_NUEVA  = CRED_PASS        # <<< MISMA contraseña para probar reutilización

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

    # Si ya está logueado por sesión previa
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


# ============ ACTUALIZAR CONTRASEÑA + EVALUAR REUTILIZACIÓN ============
def cambiar_contrasena(driver, pass_actual, pass_nueva, evaluar_reutilizacion=False):
    """
    Usa la vista /perfil para actualizar la contraseña:
      - Llena Contraseña actual, Nueva y Confirmar.
      - Clic en Guardar.

    Si evaluar_reutilizacion=True, intenta deducir:
      - Si el sistema permite o no usar la MISMA contraseña.

    Devuelve:
      - True  -> permite reutilizar
      - False -> NO permite reutilizar
      - None  -> no se pudo determinar automáticamente
    """
    log("Navegando a la vista Perfil…")
    driver.get(PERFIL_URL)
    wait_loader(driver)

    wait = WebDriverWait(driver, 15)

    # Asegurar que la sección exista
    header = wait.until(
        EC.visibility_of_element_located(
            (By.XPATH, "//h2[normalize-space()='Actualizar contraseña']")
        )
    )
    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", header)
    sleep(1)

    # Formulario específico de contraseña (action /password)
    form = wait.until(
        EC.presence_of_element_located(
            (By.XPATH, "//form[@action='https://reportfia.deras.dev/password']")
        )
    )

    campo_actual = form.find_element(By.ID, "update_password_current_password")
    campo_nueva = form.find_element(By.ID, "update_password_password")
    campo_conf  = form.find_element(By.ID, "update_password_password_confirmation")

    log("Llenando campos de contraseña actual, nueva y confirmación…")
    campo_actual.clear()
    campo_actual.send_keys(pass_actual)

    campo_nueva.clear()
    campo_nueva.send_keys(pass_nueva)

    campo_conf.clear()
    campo_conf.send_keys(pass_nueva)

    # Botón Guardar dentro de ese formulario
    btn_guardar = form.find_element(By.XPATH, ".//button[@type='submit']")
    log("Clic en 'Guardar' para actualizar contraseña…")
    btn_guardar.click()

    wait_loader(driver)
    sleep(2)

    log("Revisando mensajes en la UI luego de intentar actualizar la contraseña…")

    mensajes_ui = []

    # 1) Errores en rojo en toda la página (no solo dentro del form, por si el DOM se recarga)
    try:
        error_elems = driver.find_elements(
            By.XPATH, "//*[contains(@class,'text-red')]"
        )
        for elem in error_elems:
            txt = elem.text.strip()
            if txt:
                mensajes_ui.append(f"ERROR: {txt}")
    except Exception:
        pass

    # 2) Mensaje del notyf-announcer (si lo usa el sistema)
    try:
        announcer = driver.find_element(By.CLASS_NAME, "notyf-announcer")
        announcer_txt = announcer.text.strip()
        if announcer_txt:
            mensajes_ui.append(f"NOTYF: {announcer_txt}")
    except Exception:
        pass

    if mensajes_ui:
        log("Mensajes detectados en la interfaz después del cambio de contraseña:")
        for m in mensajes_ui:
            log(f"  → {m}")
    else:
        log("No se detectaron mensajes visibles (errores o notificaciones) en la UI.")

    # Si no queremos evaluar reutilización, solo devolvemos
    if not evaluar_reutilizacion:
        log("Evaluación de reutilización desactivada (evaluar_reutilizacion=False).")
        return None

    # Heurística para interpretar si permite reutilizar o no
    permite_reutilizar = None

    for m in mensajes_ui:
        lower = m.lower()

        # Pistas de que NO permite reutilizar
        if ("diferente" in lower or
            "no puede ser igual" in lower or
            "igual a la actual" in lower):
            permite_reutilizar = False

        # Pistas de éxito (posible que sí lo permita si no hay regla)
        if ("contraseña actualizada" in lower or
            "contraseña actualizada correctamente" in lower or
            ("notyf:" in lower and "éxito" in lower)):
            if permite_reutilizar is None:
                permite_reutilizar = True

    # Log de resultado
    if permite_reutilizar is True:
        log("🔎 Resultado prueba reutilización: EL SISTEMA SÍ permite usar la misma contraseña que la anterior.")
    elif permite_reutilizar is False:
        log("🔎 Resultado prueba reutilización: EL SISTEMA NO permite usar la misma contraseña que la anterior (regla de seguridad aplicada).")
    else:
        log("🔎 Resultado prueba reutilización: No se pudo determinar automáticamente si el sistema permite reutilizar la misma contraseña.")
        log("   Sugerencia: revisa visualmente la página o el screenshot generado si hubo error.")

    return permite_reutilizar


def logout(driver):
    """
    Cierra la sesión usando el menú de usuario (dropdown con botón 'Salir').
    """
    log("Iniciando cierre de sesión…")

    if not is_logged_in(driver, timeout=3):
        log("No se detecta navbar; parece que ya no hay sesión activa.")
        return

    wait = WebDriverWait(driver, 15)

    # Navbar
    try:
        wait.until(
            EC.presence_of_element_located(
                (By.XPATH, "//nav[contains(@class,'fixed') and contains(@class,'z-50')]")
            )
        )
    except TimeoutException:
        screenshot(driver, "sin_navbar_logout")
        raise TimeoutException("No se encontró navbar para cerrar sesión.")

    # Botón que abre el dropdown del usuario
    try:
        menu_btn = wait.until(
            EC.element_to_be_clickable(
                (By.CSS_SELECTOR, "button[data-dropdown-toggle='dropdown-user']")
            )
        )
        log("Clic en botón de menú de usuario…")
        menu_btn.click()
    except TimeoutException:
        screenshot(driver, "sin_boton_dropdown_user")
        raise TimeoutException("No se encontró el botón de menú de usuario para cerrar sesión.")

    # Botón "Salir"
    try:
        btn_salir = wait.until(
            EC.element_to_be_clickable(
                (By.XPATH,
                 "//div[@id='dropdown-user']//form[@action='https://reportfia.deras.dev/logout']//button")
            )
        )
        log("Clic en 'Salir' para cerrar sesión…")
        btn_salir.click()
    except TimeoutException:
        screenshot(driver, "sin_boton_salir")
        raise TimeoutException("No se encontró el botón 'Salir' en el dropdown de usuario.")

    wait_loader(driver)

    if is_logged_in(driver, timeout=3):
        screenshot(driver, "navbar_presente_tras_logout")
        raise TimeoutException("Tras intentar cerrar sesión, el navbar sigue presente (logout fallido).")

    log("✅ Sesión cerrada correctamente.")


# ========================== MAIN ==========================
if __name__ == "__main__":
    driver = new_driver()
    try:
        log("⚙️ Caso de prueba: Actualizar contraseña usando la MISMA contraseña actual.")
        iniciar_sesion(driver, CRED_USUARIO, CRED_PASS)

        evaluar_reutilizacion = (PASS_ACTUAL == PASS_NUEVA)
        resultado = cambiar_contrasena(
            driver,
            PASS_ACTUAL,
            PASS_NUEVA,
            evaluar_reutilizacion=evaluar_reutilizacion
        )

        if evaluar_reutilizacion:
            if resultado is True:
                log("✅ CONCLUSIÓN: El sistema PERMITE reutilizar la misma contraseña.")
            elif resultado is False:
                log("✅ CONCLUSIÓN: El sistema NO permite reutilizar la misma contraseña (comportamiento esperado a nivel de seguridad).")
            else:
                log("⚠️ CONCLUSIÓN: No se pudo determinar automáticamente. Revisa los mensajes en la interfaz o los screenshots.")
        else:
            log("Nota: Para evaluar reutilización, PASS_ACTUAL y PASS_NUEVA deben ser iguales.")

        # 🔁 Validación adicional: cerrar sesión e intentar entrar con la contraseña "nueva"
        log("🔁 Validación de re-login con la contraseña configurada...")
        try:
            logout(driver)
            log("Intentando iniciar sesión con la contraseña configurada en el cambio...")
            iniciar_sesion(driver, CRED_USUARIO, PASS_NUEVA)
            if is_logged_in(driver):
                log("🔁 Re-login: se pudo iniciar sesión con la contraseña configurada en la actualización.")
            else:
                log("🔁 Re-login: NO se pudo iniciar sesión con la contraseña configurada en la actualización.")
        except Exception as e2:
            log(f"⚠️ Error durante la validación de re-login: {e2}")
            screenshot(driver, "error_relogin")

        sleep(5)

    except Exception as e:
        log(f"❌ Error en el flujo general: {e}")
        screenshot(driver, "error_login_o_cambio_pass")
        raise
    finally:
        driver.quit()
