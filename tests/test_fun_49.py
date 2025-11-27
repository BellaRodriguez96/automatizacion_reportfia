from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
import time, os, random, string
from datetime import datetime, timedelta

# ======================
#  VARIABLES GLOBALES
# ======================
BASE_URL = "https://reportfia.deras.dev/iniciar-sesion"
URL_INICIO = "https://reportfia.deras.dev/inicio"
USER_CARNET = "aa11001"
USER_PASSWORD = "pass123"
NOMBRE = "Recurso de Prueba " + ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))

CHROME_PROFILE_DIR = os.path.abspath("./.chrome-profile-reportfia")
CHROME_SUBPROFILE = "ReportFIAProfile"

# ======================
#  UTILIDADES GENERALES
# ======================

def make_driver():
    """Inicia Chrome con perfil persistente para evitar 2FA."""
    options = webdriver.ChromeOptions()
    options.add_argument(f"--user-data-dir={CHROME_PROFILE_DIR}")
    options.add_argument(f"--profile-directory={CHROME_SUBPROFILE}")
    options.add_argument("--start-maximized")
    return webdriver.Chrome(options=options)

# ======================
#  EJECUCIÓN PRINCIPAL
# ======================

driver = make_driver()
wait = WebDriverWait(driver, 15)

try:
    print("🚀 INICIANDO PRUEBA FUN-49 - Registro de un nuevo recurso")
    driver.get(BASE_URL)
    driver.maximize_window()
    time.sleep(1)

    # LOGIN (si no existe sesión previa)
    if URL_INICIO in driver.current_url:
        print("✔ Sesión ya iniciada, saltando login...")
    else:
        input_user = wait.until(EC.presence_of_element_located((By.ID, "carnet")))
        input_pass = wait.until(EC.presence_of_element_located((By.ID, "password")))
        input_user.send_keys(USER_CARNET)
        input_pass.send_keys(USER_PASSWORD)
        driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        time.sleep(0.5)

    # NAVEGAR: Mantenimiento → Recursos
    print("📂 Abriendo menú Mantenimientos...")
    wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button[data-collapse-toggle='mantenimientos-dropdown']"))).click()
    time.sleep(0.5)

    print("✔ Menú Mantenimientos desplegado")
    wait.until(EC.element_to_be_clickable((
        By.CSS_SELECTOR,
        "a[href='/mantenimientos/recursos'], a[href='https://reportfia.deras.dev/mantenimientos/recursos']"
    ))).click()

    print("✔ Navegado a Mantenimiento → Recursos")
    time.sleep(0.5)

    print("📎 Abriendo modal 'Añadir Recursos'...")

    btn_add = wait.until(
        EC.element_to_be_clickable((
            By.CSS_SELECTOR,
            "button[data-modal-toggle='static-modal'], button[data-modal-target='static-modal']"
        ))
    )

    driver.execute_script("arguments[0].scrollIntoView(false);", btn_add)
    time.sleep(0.2)

    try:
        btn_add.click()
    except:
        driver.execute_script("arguments[0].click();", btn_add)

    print("✔ Modal abierto correctamente")
    time.sleep(0.5)

    # ========= LLENAR FORMULARIO =========
    # Nombre
    wait.until(EC.presence_of_element_located((By.NAME, "nombre"))).send_keys(NOMBRE)
    time.sleep(0.2)

    #Estado
    select_estado = wait.until(
        EC.element_to_be_clickable((By.ID, "activo"))
    )
    sel = Select(select_estado)
    sel.select_by_value("1")  # ACTIVO

    print("🎉 FORMULARIO ENVIADO CON ÉXITO")

    # Guardar
    print("💾 Guardando nuevo recurso...")

    btn_guardar = wait.until(
        EC.element_to_be_clickable((
            By.CSS_SELECTOR,
            "button[type='submit'][form='recurso-form']"
        ))
    )

    driver.execute_script("arguments[0].scrollIntoView(false);", btn_guardar)
    time.sleep(0.25)

    try:
        btn_guardar.click()
    except:
        driver.execute_script("arguments[0].click();", btn_guardar)

    print("✔ Recurso guardado correctamente")

    time.sleep(2)

    # Notificación
    try:
        notyf = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.notyf__message")))
        print("✔ Notificación:", notyf.text)
    except:
        print("⚠ No apareció notificación, continuando…")

    wait.until(EC.url_contains("/mantenimientos/recursos"))
    print("✔ Regresó a Mantenimiento -> recursoss")

    # ========= BUSCAR EL RECURSO =========
    print("🔎 Buscando el recurso recién creado...")

    filtro = wait.until(EC.element_to_be_clickable((By.ID, "nombre-filter")))
    driver.execute_script("arguments[0].value='';", filtro)
    filtro.send_keys(NOMBRE)
    time.sleep(0.2)

    print("🔎 Ejecutando búsqueda en tabla...")

    btn_buscar = wait.until(EC.element_to_be_clickable((
        By.CSS_SELECTOR,
        "button[data-tooltip-target='tooltip-aplicar-filtros']"
    )))

    driver.execute_script("arguments[0].scrollIntoView(false);", btn_buscar)
    time.sleep(0.2)

    try:
        btn_buscar.click()
        print("✔ Búsqueda ejecutada con click normal")
    except:
        print("⚠ Click interceptado, usando click por JavaScript")
        driver.execute_script("arguments[0].click();", btn_buscar)

    print("✔ Búsqueda ejecutada correctamente")
    time.sleep(10)

finally:
    print("Cerrando navegador…")
    driver.quit()
