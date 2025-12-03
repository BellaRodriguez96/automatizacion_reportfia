# -*- coding: utf-8 -*-
import os
import base64
import tempfile
from time import sleep
from datetime import datetime

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException


# ========= CONFIG =========
LOGIN_URL = "https://reportfia.deras.dev/iniciar-sesion"
BASE_URL  = "https://reportfia.deras.dev/reportes/registrar"  # corregida

# Credenciales válidas (AJUSTA el usuario si es otro)
CRED_USUARIO  = "AA11001"
CRED_PASSWORD = "pass123"   # <<< aclarado en tu mensaje

# Datos del reporte (ajusta si quieres)
TIPO_INCIDENCIA_TEXTO = "Problemas con baños"  # Debe coincidir con una opción del dropdown
DESCRIPCION_TEXTO     = "Inodoro con fuga de agua en el aula C11."
LUGAR_TEXTO           = "C11"

# Persistencia del “dispositivo” (perfil de Chrome): el 2FA se pedirá solo la primera vez
CHROME_PROFILE_DIR = os.path.abspath("./.chrome-profile-reportfia")
CHROME_SUBPROFILE  = "ReportFIAProfile"

# ¿Enviar realmente el formulario al backend?
ENVIAR_REALMENTE = True
# =========================


def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")


def crear_imagen_temporal():
    """Crea un PNG mínimo (1x1) por Base64 (sin Pillow)."""
    png_1x1 = (
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR4nGNgYAAAAAMA"
        "ASsJTYQAAAAASUVORK5CYII="
    )
    ruta = os.path.join(tempfile.gettempdir(), "evidencia_test.png")
    with open(ruta, "wb") as f:
        f.write(base64.b64decode(png_1x1))
    return ruta


def make_driver():
    log("Creando Chrome con perfil persistente…")
    options = webdriver.ChromeOptions()
    options.add_argument(f"--user-data-dir={CHROME_PROFILE_DIR}")
    options.add_argument(f"--profile-directory={CHROME_SUBPROFILE}")
    options.add_argument("--start-maximized")
    # options.add_argument("--headless=new")  # opcional: comenta si necesitas ver el navegador
    options.page_load_strategy = "normal"
    return webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)


def wait_for_loader_to_hide(driver, timeout=20):
    """Espera a que el overlay #loader esté oculto/no presente (evita clics bloqueados)."""
    try:
        WebDriverWait(driver, timeout).until(
            EC.any_of(
                EC.invisibility_of_element_located((By.ID, "loader")),
                EC.visibility_of_any_elements_located((By.TAG_NAME, "body")),  # fallback
            )
        )
    except Exception:
        log("⚠️ No se pudo confirmar invisibilidad de #loader (continuando).")


def screenshot(driver, name="debug"):
    ruta = os.path.abspath(f"./{name}_{datetime.now().strftime('%H%M%S')}.png")
    try:
        driver.save_screenshot(ruta)
        log(f"📸 Screenshot guardado: {ruta}")
    except Exception as e:
        log(f"⚠️ No se pudo guardar screenshot: {e}")


def is_logged_in(driver, short_timeout=4):
    """Devuelve True si detecta el navbar fijo (layout autenticado)."""
    try:
        WebDriverWait(driver, short_timeout).until(
            EC.presence_of_element_located((By.XPATH, "//nav[contains(@class,'fixed') and contains(@class,'z-50')]"))
        )
        return True
    except TimeoutException:
        return False


def manejar_posible_2fa(driver):
    """Si hay input de código, pedirlo por consola; si no, salir tranquilo."""
    log("Chequeando si apareció 2FA…")
    try:
        code_input = WebDriverWait(driver, 3).until(
            EC.presence_of_element_located((
                By.XPATH,
                "//input[(contains(@id,'code') or contains(@name,'code')) or "
                "contains(translate(@placeholder,'ÓÓ','oo'),'codigo') or "
                "contains(translate(@placeholder,'ÓÓ','oo'),'código')]"
            ))
        )
    except TimeoutException:
        log("No hay 2FA (dispositivo ya confiado).")
        return

    log("🔐 2FA detectado. Ingresa el código recibido por correo.")
    otp = input("Código 2FA: ").strip()
    if not otp:
        raise RuntimeError("No se ingresó un código 2FA.")

    code_input.clear()
    code_input.send_keys(otp)

    # Confirmar
    btn_confirm = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((
            By.XPATH,
            "//button[contains(.,'Verificar') or contains(.,'Confirmar') or contains(.,'Continuar')]"
        ))
    )
    btn_confirm.click()
    wait_for_loader_to_hide(driver, timeout=20)

    # Validar navbar tras 2FA
    if not is_logged_in(driver, short_timeout=10):
        screenshot(driver, "no_navbar_post_2fa")
        raise TimeoutException("No se detectó navbar tras enviar el 2FA.")
    log("✅ 2FA completado; el dispositivo quedará confiado.")


def iniciar_sesion(driver, usuario, password):
    log("Navegando a LOGIN_URL…")
    driver.get(LOGIN_URL)
    wait_for_loader_to_hide(driver)
    log(f"URL actual tras GET: {driver.current_url}")

    # Caso 1: ya estamos logueados (por perfil persistente)
    if is_logged_in(driver, short_timeout=4):
        log("Sesión ya iniciada (navbar detectado). Saltando login.")
        return

    log("Buscando login form o navbar…")
    # Esperar EITHER: login form visible OR navbar (por si el server redirige a /inicio)
    try:
        WebDriverWait(driver, 12).until(
            EC.any_of(
                EC.visibility_of_element_located((By.ID, "loginForm")),
                EC.presence_of_element_located((By.XPATH, "//nav[contains(@class,'fixed') and contains(@class,'z-50')]"))
            )
        )
    except TimeoutException:
        screenshot(driver, "no_login_form")
        raise TimeoutException("No se encontró ni el formulario de login ni el navbar (revisa el screenshot).")

    # Si ya estamos autenticados aquí, salimos
    if is_logged_in(driver, short_timeout=1):
        log("Sesión detectada después del primer wait. Saltando login.")
        return

    # Caso 2: sí hay formulario → completar credenciales
    log("Ingresando credenciales…")
    carnet_input = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, "carnet")))
    pass_input   = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, "password")))

    carnet_input.clear(); carnet_input.send_keys(usuario)
    pass_input.clear();   pass_input.send_keys(password)

    # Recordarme (opcional)
    try:
        remember = driver.find_element(By.ID, "remember_me")
        if not remember.is_selected():
            remember.click()
    except Exception:
        pass

    log("Click en Iniciar sesión…")
    driver.find_element(By.XPATH, "//button[normalize-space()='Iniciar sesión' and @type='submit']").click()
    wait_for_loader_to_hide(driver, timeout=20)

    # Esperar EITHER: 2FA o navbar (sesión completa)
    log("Esperando 2FA o layout autenticado…")
    try:
        WebDriverWait(driver, 12).until(
            EC.any_of(
                EC.presence_of_element_located((
                    By.XPATH,
                    "//input[(contains(@id,'code') or contains(@name,'code')) or "
                    "contains(translate(@placeholder,'ÓÓ','oo'),'codigo') or "
                    "contains(translate(@placeholder,'ÓÓ','oo'),'código')]"
                )),
                EC.presence_of_element_located((By.XPATH, "//nav[contains(@class,'fixed') and contains(@class,'z-50')]"))
            )
        )
    except TimeoutException:
        screenshot(driver, "despues_de_login_sin_2fa_ni_navbar")
        raise TimeoutException("Tras login no apareció 2FA ni navbar (ver screenshot).")

    # Si hay 2FA, pedirlo una sola vez (primer run con este perfil). Si no, seguimos.
    manejar_posible_2fa(driver)

    # Confirmar que ya estamos autenticados
    if not is_logged_in(driver, short_timeout=10):
        screenshot(driver, "no_navbar_despues_2fa")
        raise TimeoutException("No se detectó navbar tras 2FA/login.")
    log("Sesión iniciada correctamente.")


def abrir_formulario_reporte(driver):
    log("Navegando al formulario de reporte…")
    driver.get(BASE_URL)  # navegación explícita SIEMPRE tras login
    wait_for_loader_to_hide(driver)

    log("Esperando el título 'Reportar una incidencia'…")
    WebDriverWait(driver, 20).until(
        EC.visibility_of_element_located(
            (By.XPATH, "//*[contains(@class,'text-2xl') and contains(.,'Reportar una incidencia')]")
        )
    )


def seleccionar_tipo_incidencia(driver, texto_visible):
    log(f"Seleccionando tipo de incidencia: {texto_visible}")
    buscador = WebDriverWait(driver, 15).until(
        EC.element_to_be_clickable((By.ID, "search-id_tipo_incidencia"))
    )
    buscador.click()
    buscador.clear()
    buscador.send_keys(texto_visible)

    opcion = WebDriverWait(driver, 15).until(
        EC.element_to_be_clickable(
            (By.XPATH, f"//ul[@id='dropdown-id_tipo_incidencia']//li[contains(normalize-space(), '{texto_visible}')]")
        )
    )
    opcion.click()

    hidden = driver.find_element(By.ID, "id_tipo_incidencia")
    WebDriverWait(driver, 5).until(lambda d: hidden.get_attribute("value") != "")


def escribir_descripcion(driver, texto):
    log("Escribiendo descripción…")
    descripcion = WebDriverWait(driver, 15).until(
        EC.element_to_be_clickable((By.ID, "descripcion"))
    )
    descripcion.click()
    descripcion.clear()
    descripcion.send_keys(texto)


def seleccionar_lugar(driver, texto_lugar):
    log(f"Seleccionando lugar: {texto_lugar}")
    lugar_input = WebDriverWait(driver, 15).until(
        EC.element_to_be_clickable((By.ID, "lugar-input"))
    )
    lugar_input.click()
    lugar_input.clear()
    lugar_input.send_keys(texto_lugar)

    opcion = WebDriverWait(driver, 15).until(
        EC.element_to_be_clickable((
            By.XPATH,
            f"//div[contains(@class,'z-10') and contains(@class,'shadow-lg')]"
            f"//li[.//span[normalize-space()='{texto_lugar}']]"
        ))
    )
    opcion.click()

    WebDriverWait(driver, 5).until(
        lambda d: d.find_element(By.ID, "lugar-input").get_attribute("value").strip() == texto_lugar
    )


def subir_evidencia(driver, ruta_archivo):
    log("Subiendo evidencia…")
    # Hacer visible el input oculto
    driver.execute_script("""
      const input = document.getElementById('comprobantes');
      if (input) { input.classList.remove('hidden'); input.style.display='block'; }
    """)

    file_input = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "comprobantes"))
    )
    file_input.send_keys(ruta_archivo)

    # Verificar que desaparezca el placeholder #empty
    WebDriverWait(driver, 10).until(EC.invisibility_of_element_located((By.ID, "empty")))


def abrir_modal_envio(driver):
    log("Abriendo modal de envío…")
    btn_enviar = WebDriverWait(driver, 20).until(
        EC.element_to_be_clickable(
            (By.XPATH, "//button[contains(.,'Enviar reporte') and not(@disabled)]")
        )
    )
    btn_enviar.click()
    wait_for_loader_to_hide(driver)


def confirmar_envio(driver, enviar_realmente=False):
    log("Confirmando envío (manejando duplicidad si aplica)…")

    # Esperar que se abra cualquiera de los dos modales
    try:
        WebDriverWait(driver, 10).until(
            EC.any_of(
                EC.visibility_of_element_located((By.ID, "send-modal")),
                EC.visibility_of_element_located((By.XPATH, "//*[contains(@class,'sm:max-w-lg') and .//h2[contains(.,'Advertencia de Duplicidad')]]"))
            )
        )
    except TimeoutException:
        screenshot(driver, "modal_no_aparecio")
        raise TimeoutException("No apareció ni el modal de envío ni el de duplicidad.")

    # Si aparece el modal de duplicidad, pulsar "Proceder"
    try:
        btn_proceder = WebDriverWait(driver, 2).until(
            EC.element_to_be_clickable((By.ID, "confirm-force-send"))
        )
        btn_proceder.click()
        wait_for_loader_to_hide(driver)
        log("Se confirmó envío a pesar de duplicidad.")
    except Exception:
        pass  # No había duplicidad

    # Ahora debe estar el modal de envío visible
    try:
        WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.ID, "send-modal"))
        )
    except TimeoutException:
        screenshot(driver, "send_modal_no_visible")
        raise TimeoutException("No se hizo visible el modal de envío.")

    # Botón Enviar (type='submit') dentro del modal
    btn_submit = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((
            By.XPATH,
            "//div[@id='send-modal']//button[@type='submit' and contains(.,'Enviar')]"
        ))
    )

    if not enviar_realmente:
        log("ℹ️ Modal listo; envío real desactivado (cambia ENVIAR_REALMENTE=True si quieres enviar).")
        return

    # Clic en Enviar
    btn_submit.click()
    wait_for_loader_to_hide(driver, timeout=20)
    log("✔️ Click de envío realizado.")

    # Verificación de resultado: intenta detectar redirect o toast de éxito
    enviado = False
    try:
        # 1) Redirect típico post-envío (ajusta si tu app redirige a otra ruta)
        WebDriverWait(driver, 8).until(
            EC.any_of(
                EC.url_contains("/reportes/mis-reportes"),
                EC.url_contains("/reportes/listado-general"),
                EC.url_contains("/reportes")  # fallback
            )
        )
        enviado = True
    except TimeoutException:
        # 2) Notyf de éxito (si lo usan tras enviar)
        try:
            WebDriverWait(driver, 4).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".notyf, .notyf__toast"))
            )
            enviado = True
        except TimeoutException:
            pass

    if enviado:
        log("✅ Reporte ENVIADO con éxito (redirect/toast detectado).")
    else:
        screenshot(driver, "posible_envio_fallido")
        log("⚠️ No pude confirmar el éxito del envío. Revisa el screenshot y la consola.")


if __name__ == "__main__":
    evidencia = crear_imagen_temporal()
    driver = make_driver()
    try:
        iniciar_sesion(driver, CRED_USUARIO, CRED_PASSWORD)

        # MUY IMPORTANTE: navegar SIEMPRE al formulario tras el login
        abrir_formulario_reporte(driver)

        seleccionar_tipo_incidencia(driver, TIPO_INCIDENCIA_TEXTO)
        escribir_descripcion(driver, DESCRIPCION_TEXTO)
        seleccionar_lugar(driver, LUGAR_TEXTO)
        subir_evidencia(driver, evidencia)
        abrir_modal_envio(driver)
        confirmar_envio(driver, enviar_realmente=ENVIAR_REALMENTE)

        log("✅ Flujo completado.")
    except Exception as e:
        log(f"❌ Error en la prueba: {e}")
        screenshot(driver, "error")
        raise
    finally:
        sleep(2)
        driver.quit()
        try:
            os.remove(evidencia)
        except Exception:
            pass
