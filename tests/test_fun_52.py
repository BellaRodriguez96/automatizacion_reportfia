# -*- coding: utf-8 -*-
from time import sleep
from datetime import datetime
import os
import re

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

# ========= CONFIG =========
LOGIN_URL    = "https://reportfia.deras.dev/iniciar-sesion"
RECURSOS_URL = "https://reportfia.deras.dev/mantenimientos/recursos"

CRED_USUARIO = "AA11001"
CRED_PASS    = "pass123"

# Carpeta donde se guarda el perfil de Chrome (cookies, “dispositivo de confianza”, etc.)
CHROME_PROFILE_DIR = os.path.abspath("./chrome-profile-reportfia")

# Ruta de la plantilla de Excel con los recursos a importar
PLANTILLA_RECURSOS_XLSX = os.path.abspath("./RECURSOS.xlsx")
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

    # Si ya está logueado por sesión previa, solo lo dejamos así
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

    carnet.clear()
    carnet.send_keys(usuario)
    clave.clear()
    clave.send_keys(password)

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


# ========================
# FUNCIONES PARA RECURSOS
# ======================

def contar_filas_tabla_recursos(driver, timeout=10):
    """
    Cuenta las filas visibles en la tabla de recursos
    (solo la página actual, por logging).
    """
    try:
        filas = WebDriverWait(driver, timeout).until(
            EC.presence_of_all_elements_located(
                (By.XPATH, "//table//tbody/tr")
            )
        )
        return len(filas)
    except TimeoutException:
        screenshot(driver, "sin_filas_tabla_recursos")
        raise TimeoutException("No se encontraron filas en la tabla de recursos.")


def get_total_recursos(driver):
    """
    Lee el texto del paginador:
    'Mostrando del 1 al 10 de un total de 52 resultados'
    y devuelve el número total (52).
    """
    try:
        p = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located(
                (By.XPATH, "//p[contains(normalize-space(),'de un total de')]")
            )
        )
        texto = p.text  # ej: "Mostrando del 1 al 10 de un total de 52 resultados"
        m = re.search(r"de un total de\s+(\d+)", texto)
        if not m:
            raise ValueError(f"No se pudo extraer el total de resultados del texto: {texto}")
        return int(m.group(1))
    except TimeoutException:
        screenshot(driver, "sin_paginador_recursos")
        raise TimeoutException(
            "No se encontró el texto de paginación con 'de un total de' en la página de Recursos."
        )


def importar_recursos(driver, ruta_excel=PLANTILLA_RECURSOS_XLSX):
    """
    Caso de prueba automatizado:
    - Ir a la pantalla de Recursos.
    - Obtener TOTAL de recursos desde el paginador.
    - Clic en 'Importar datos' (abre modal).
    - Cargar archivo Excel en #excel_file.
    - Clic en botón 'Guardar' (type=submit, form='import-excel-recursos').
    - Verificar que el TOTAL de recursos aumente.
    """
    log("== Caso de prueba: Importar recursos desde plantilla Excel ==")

    if not os.path.exists(ruta_excel):
        raise FileNotFoundError(
            f"No se encontró la plantilla de Excel para recursos en: {ruta_excel}\n"
            f"Asegúrate de colocar ahí el archivo o de cambiar la ruta en PLANTILLA_RECURSOS_XLSX."
        )

    log(f"Abriendo página de Recursos: {RECURSOS_URL}")
    driver.get(RECURSOS_URL)
    wait_loader(driver)

    # Solo para logging: filas visibles en la página actual
    filas_antes = contar_filas_tabla_recursos(driver)
    log(f"Filas visibles en la página de recursos ANTES de importar: {filas_antes}")

    # Valor real que usaremos para la aserción: total de resultados
    total_antes = get_total_recursos(driver)
    log(f"TOTAL de recursos ANTES de importar: {total_antes}")

    # Clic en el botón "Importar datos"
    try:
        btn_importar = WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable(
                (By.XPATH, "//button[contains(normalize-space(),'Importar datos')]")
            )
        )
    except TimeoutException:
        screenshot(driver, "sin_boton_importar_datos_recursos")
        raise TimeoutException(
            "No se encontró el botón 'Importar datos' en la pantalla de Recursos."
        )

    log("Clic en botón 'Importar datos'…")
    btn_importar.click()

    # Esperar a que el modal de Excel sea visible
    try:
        WebDriverWait(driver, 15).until(
            EC.visibility_of_element_located((By.ID, "static-modal-excel"))
        )
    except TimeoutException:
        screenshot(driver, "modal_excel_no_visible")
        raise TimeoutException("No se abrió el modal de importación de recursos (static-modal-excel).")

    # Input file dentro del modal (id="excel_file")
    try:
        input_file = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.ID, "excel_file"))
        )
    except TimeoutException:
        screenshot(driver, "sin_input_excel_recursos")
        raise TimeoutException("No se encontró el campo para subir el archivo Excel (id='excel_file').")

    log(f"Adjuntando archivo Excel: {ruta_excel}")
    input_file.send_keys(ruta_excel)

    # Botón Guardar está FUERA del form, pero asociado por form="import-excel-recursos"
    try:
        btn_guardar = WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable(
                (By.CSS_SELECTOR, "button[type='submit'][form='import-excel-recursos']")
            )
        )
    except TimeoutException:
        try:
            btn_guardar = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable(
                    (By.XPATH,
                     "//button[@type='submit' and @form='import-excel-recursos'"
                     " and contains(normalize-space(),'Guardar')]")
                )
            )
        except TimeoutException:
            screenshot(driver, "sin_boton_guardar_import_recursos")
            raise TimeoutException(
                "No se encontró el botón 'Guardar' del modal de importación de recursos."
            )

    log("Clic en botón 'Guardar' del modal de importación…")
    btn_guardar.click()
    wait_loader(driver)

    # Pequeña espera adicional por si el backend procesa el archivo
    sleep(3)

    # Recargar la página para asegurarnos de ver la tabla + paginador actualizados
    driver.get(RECURSOS_URL)
    wait_loader(driver)

    filas_despues = contar_filas_tabla_recursos(driver)
    log(f"Filas visibles en la página de recursos DESPUÉS de importar: {filas_despues}")

    total_despues = get_total_recursos(driver)
    log(f"TOTAL de recursos DESPUÉS de importar: {total_despues}")

    # La aserción ahora se hace sobre el total, no sobre las filas de la página
    if total_despues <= total_antes:
        screenshot(driver, "sin_cambios_import_recursos")
        raise AssertionError(
            f"Se esperaba que el TOTAL de recursos aumentara tras la importación, "
            f"pero total_antes={total_antes}, total_despues={total_despues}."
        )

    log("✅ Importación de recursos desde Excel completada correctamente "
        "(se incrementó el TOTAL de recursos).")


if __name__ == "__main__":
    driver = new_driver()
    try:
        iniciar_sesion(driver, CRED_USUARIO, CRED_PASS)
        log("🔵 Deberías ver ReportFIA ya autenticado.")
        importar_recursos(driver)
        log("✅ Flujo completo de importación de recursos finalizado correctamente.")
        sleep(5)
    except Exception as e:
        log(f"❌ Error en el flujo completo: {e}")
        screenshot(driver, "error_importar_recursos")
        raise
    finally:
        driver.quit()
