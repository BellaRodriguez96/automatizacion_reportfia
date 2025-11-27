from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time, re, os
from selenium.webdriver.common.keys import Keys
import shutil
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager


# 🌐 VARIABLES GLOBALES
BASE_URL = "https://reportfia.deras.dev/iniciar-sesion"
USER_CARNET = "aa11001"
USER_PASSWORD = "pass123"
YOPMAIL_URL = "https://yopmail.com/es/"
URL_INICIO = "https://reportfia.deras.dev/inicio"
# Persistencia del “dispositivo” (perfil de Chrome): el 2FA se pedirá solo la primera vez
CHROME_PROFILE_DIR = os.path.abspath("./.chrome-profile-reportfia")
CHROME_SUBPROFILE  = "ReportFIAProfile"

# ==========================================================
#   FUNCIÓN: VALIDAR LOGIN EXITOSO
# ==========================================================
def validar_login_exitoso():
    time.sleep(0.5)
    if URL_INICIO in driver.current_url:
        print("🎉 CASO PASÓ: Se llegó a /inicio correctamente")
        return True
    return False

# ==========================================================
#   FUNCIÓN: LIMPIAR SESION PREVIA
# ==========================================================
def limpiar_perfil_chrome():
    if os.path.exists(CHROME_PROFILE_DIR):
        print("🧹 Eliminando perfil persistente de Chrome…")
        shutil.rmtree(CHROME_PROFILE_DIR, ignore_errors=True)
    else:
        print("✔ No existe perfil previo, nada que limpiar")

# ==========================================================
#   FUNCIÓN: ABRIR YOPMAIL Y OBTENER CÓDIGO
# ==========================================================
def abrir_yopmail_y_obtener_codigo(carnet):

    # 🔒 Asegurar que existe la pestaña principal
    if len(driver.window_handles) == 0:
        raise Exception("❌ No existe ninguna pestaña activa en Chrome")

    # 🔒 Siempre volver a la pestaña principal antes de abrir Yopmail
    driver.switch_to.window(driver.window_handles[0])
    time.sleep(0.5)

    # 🆕 ABRIR UNA NUEVA PESTAÑA PARA YOPMAIL
    driver.execute_script("window.open('about:blank', '_blank');")
    time.sleep(0.5)

    # Cambiar a la nueva pestaña
    nueva_pestana = driver.window_handles[-1]
    driver.switch_to.window(nueva_pestana)

    print("🆕 Nueva pestaña abierta para Yopmail")

    # Ir a Yopmail
    driver.get(YOPMAIL_URL)
    if "yopmail.com/es/wm" in driver.current_url or "yopmail.com/es/inbox" in driver.current_url:
        driver.get(YOPMAIL_URL)
        time.sleep(0.5)

    # INGRESAR CORREO
    campo = wait.until(EC.presence_of_element_located((By.ID, "login")))
    campo.clear()
    campo.send_keys(carnet)

    # --- Localizar el input YA LLENO ---
    campo = wait.until(EC.element_to_be_clickable((By.ID, "login")))

    # --- HACER FOCUS ---
    driver.execute_script("arguments[0].focus();", campo)
    time.sleep(0.2)

    # --- SOLO ENVIAR ENTER ---
    campo.send_keys(Keys.ENTER)
    print("✔ ENTER enviado → Abriendo bandeja...")
    time.sleep(0.5)

    # --- DETECTAR IFRAME CORRECTO ---
    iframes = driver.find_elements(By.TAG_NAME, "iframe")

    iframe_encontrado = False
    for i, f in enumerate(iframes):
        name = f.get_attribute("name")
        id_ = f.get_attribute("id")
        
        if name == "ifmail" or id_ == "ifmail":
            driver.switch_to.frame(f)
            iframe_encontrado = True
            print(f"✔ Entramos al iframe correcto (index={i})")
            break

    if not iframe_encontrado:
        raise Exception("❌ No se encontró el iframe del correo (ifmail)")

    time.sleep(0.5)

    # --- INTENTAR CAPTURAR EL CÓDIGO ---
    try:
        strong_el = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "#mail strong"))
        )
        codigo = strong_el.text.strip()
        print("✔ Código encontrado:", codigo)

    except:
        # Fallback: buscar cualquier número de 6 dígitos
        print("⚠ Selector #mail strong falló, buscando código con regex…")
        texto = driver.find_element(By.TAG_NAME, "body").text
        import re
        match = re.search(r"\b\d{6}\b", texto)
        if match:
            codigo = match.group(0)
            print("✔ Código encontrado por regex:", codigo)
        else:
            raise Exception("❌ No se pudo encontrar el código 2FA en el correo")

    return codigo

# ==========================================================
#   FUNCIÓN: LLENAR INPUTS 2FA
# ==========================================================
def llenar_2fa(codigo):
    inputs_2fa = wait.until(
        EC.presence_of_all_elements_located((By.CSS_SELECTOR, "input[type='text'][maxlength='1']"))
    )
    for i, digit in enumerate(codigo):
        inputs_2fa[i].send_keys(digit)
        time.sleep(0.1)

    print("✔ Código escrito correctamente")

    # --- PRESIONAR VERIFICAR ---
    btn_verificar = wait.until(
        EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Verificar')]"))
    )
    btn_verificar.click()

# ==========================================================
#   FUNCIÓN: GUARDAR DRIVER CON PERFIL
# ==========================================================
def make_driver(reset_profile=False):
    if reset_profile:
        print("Limpiando perfil persistente antes de forzar el flujo completo")
        limpiar_perfil_chrome()
    print("Creando Chrome con perfil persistente…")
    options = webdriver.ChromeOptions()
    options.add_argument(f"--user-data-dir={CHROME_PROFILE_DIR}")
    options.add_argument(f"--profile-directory={CHROME_SUBPROFILE}")
    options.add_argument("--start-maximized")
    # options.add_argument("--headless=new")  # opcional: comenta si necesitas ver el navegador
    options.page_load_strategy = "normal"
    return webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)

# Iniciar WebDriver con perfil persistente (limpiando antes esta prueba)
driver = make_driver(reset_profile=True)
wait = WebDriverWait(driver, 15)

# ==========================================================
#   EJECUCIÓN PRINCIPAL
# ==========================================================
try:
    print("🚀 INICIANDO PRUEBA FUN-01 - LOGIN")
    driver.get(BASE_URL)
    driver.maximize_window()

    # Campos del login
    input_user = wait.until(EC.presence_of_element_located((By.ID, "carnet")))
    input_pass = wait.until(EC.presence_of_element_located((By.ID, "password")))

    input_user.send_keys(USER_CARNET)
    input_pass.send_keys(USER_PASSWORD)

    btn_login = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
    btn_login.click()

    time.sleep(0.5)

    # -----------------------------------------
    # ERROR DE CREDENCIALES
    # -----------------------------------------
    try:
        error_login = WebDriverWait(driver, 3).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.notyf__message"))
        )
        print("❌ CASO FALLÓ:", error_login.text)
        raise SystemExit
    except:
        print("✔ No hay error de credenciales")

    # -----------------------------------------
    # LOGIN SIN 2FA
    # -----------------------------------------
    if "two-factor" not in driver.current_url:
        if validar_login_exitoso():
            raise SystemExit

        print("❌ No hubo error, pero tampoco llegó a /inicio → FALLO")
        raise SystemExit

    # -----------------------------------------
    # LOGIN CON 2FA
    # -----------------------------------------
    print("🔐 Requiere 2FA → Enviando código...")

    try:
        btn_login = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
        btn_login.click()
        time.sleep(0.5)
        print("✔ CLICK HUMANO aplicado sobre Enviar código")

        main_window = driver.current_window_handle

    except Exception as e:
        print("❌ NO se pudo presionar el botón Enviar código:", e)
        raise

    codigo = abrir_yopmail_y_obtener_codigo(USER_CARNET)

    # Volver a pestaña principal
    driver.switch_to.window(main_window)
    time.sleep(0.5)

    llenar_2fa(codigo)

    # Verificación final
    if validar_login_exitoso():
        print("🎉 CASO FUN-01 → PASSED 🎉")
        raise SystemExit
    else:
        print("❌ Después del 2FA NO llegó a /inicio → FAIL")
        raise SystemExit

except Exception as e:
    print("❌ ERROR GENERAL EN LA PRUEBA:", e)

finally:
    print("Cerrando navegador...")
    driver.quit()
