from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time, os, shutil


# 🌐 VARIABLES GLOBALES
BASE_URL = "https://reportfia.deras.dev/iniciar-sesion"
USER_CARNET = ""       # Campos vacíos
USER_PASSWORD = ""     # Campos vacíos
URL_INICIO = "https://reportfia.deras.dev/inicio"

# Directorio del perfil (que ahora solo se usará para limpiar)
CHROME_PROFILE_DIR = os.path.abspath("./.chrome-profile-reportfia")


# ==========================================================
#   LIMPIAR SESIÓN PREVIA (eliminar perfil Chrome)
# ==========================================================
def limpiar_perfil_chrome():
    if os.path.exists(CHROME_PROFILE_DIR):
        print("🧹 Eliminando perfil persistente de Chrome…")
        shutil.rmtree(CHROME_PROFILE_DIR, ignore_errors=True)
    else:
        print("✔ No existe perfil previo, nada que limpiar")


# ==========================================================
#   CREAR DRIVER SIN PERFIL PERSISTENTE
# ==========================================================
def make_driver():
    """Chrome limpio sin persistencia."""
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    return webdriver.Chrome(options=options)


# ==========================================================
#   EJECUCIÓN PRINCIPAL
# ==========================================================
limpiar_perfil_chrome()
driver = make_driver()
wait = WebDriverWait(driver, 15)

try:
    print("🚀 INICIANDO PRUEBA FUN-72 - Login con campos vacíos")
    driver.get(BASE_URL)
    driver.maximize_window()

    # Campos del login
    input_user = wait.until(
        EC.presence_of_element_located((By.ID, "carnet"))
    )
    input_pass = wait.until(
        EC.presence_of_element_located((By.ID, "password"))
    )

    # Enviar credenciales vacías
    input_user.send_keys(USER_CARNET)
    input_pass.send_keys(USER_PASSWORD)

    # Click en login
    btn_login = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
    btn_login.click()

    time.sleep(0.5)

    # ===========================================
    # 🔎 Buscar notificación de error (esperada)
    # ===========================================
    try:
        error_login = WebDriverWait(driver, 4).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.notyf__message"))
        )

        print("❌ CASO FALLÓ:", error_login.text)
        raise SystemExit  # Finalizar correctamente
    except:
        print("✔ No hay mensaje de error. (Comportamiento esperado si no carga notyf)")

finally:
    print("Cerrando navegador…")
    driver.quit()
