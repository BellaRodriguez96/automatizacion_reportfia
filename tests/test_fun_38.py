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

CHROME_PROFILE_DIR = os.path.abspath("./.chrome-profile-reportfia")
CHROME_SUBPROFILE = "ReportFIAProfile"

# ======================
#  UTILIDADES
# ======================

def make_driver():
    """Inicia Chrome con perfil persistente para evitar 2FA."""
    options = webdriver.ChromeOptions()
    options.add_argument(f"--user-data-dir={CHROME_PROFILE_DIR}")
    options.add_argument(f"--profile-directory={CHROME_SUBPROFILE}")
    options.add_argument("--start-maximized")
    return webdriver.Chrome(options=options)


def aplicar_busqueda(driver, wait):
    """Ejecuta la búsqueda del listado."""
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
        print("⚠ Click interceptado, usando JavaScript")
        driver.execute_script("arguments[0].click();", btn_buscar)

    print("✔ Búsqueda ejecutada correctamente")
    time.sleep(1)   # <-- diferencias de 1 segundo entre filtros

def scroll_to_element(driver):
    print("📜 Moviendo scroll hacia abajo...")

    # SCROLL HASTA ABAJO
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(3)

    print("📜 Moviendo scroll hacia arriba...")

    # SCROLL HASTA ARRIBA
    driver.execute_script("window.scrollTo(0, 0);")
    time.sleep(1)

    print("✔ Scroll completado")

# ======================
#  EJECUCIÓN PRINCIPAL
# ======================

driver = make_driver()
wait = WebDriverWait(driver, 15)

try:
    print("🚀 INICIANDO PRUEBA FUN-38 - Filtrado de reportes")
    driver.get(BASE_URL)
    time.sleep(1)

    # LOGIN SI ES NECESARIO
    if URL_INICIO not in driver.current_url:
        input_user = wait.until(EC.presence_of_element_located((By.ID, "carnet")))
        input_pass = wait.until(EC.presence_of_element_located((By.ID, "password")))
        input_user.send_keys(USER_CARNET)
        input_pass.send_keys(USER_PASSWORD)
        driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        time.sleep(0.5)
    else:
        print("✔ Sesión ya iniciada, saltando login...")

    # NAVEGAR A REPORTES
    print("📂 Abriendo menú Reportes...")
    wait.until(EC.element_to_be_clickable((
        By.CSS_SELECTOR,
        "button[data-collapse-toggle='reportes-dropdown']"
    ))).click()

    time.sleep(0.5)
    print("✔ Menú Reportes desplegado")

    wait.until(EC.element_to_be_clickable((
        By.CSS_SELECTOR,
        "a[href='/reportes/listado-general'], a[href='https://reportfia.deras.dev/reportes/listado-general']"
    ))).click()

    print("✔ Navegado a Reportes → Listado General")
    time.sleep(0.8)
    
    # ===============================
    #   FILTRO 1 — Últimos 7 días
    # ===============================
    # 1) Abrir el dropdown
    btn_fecha = wait.until(
        EC.element_to_be_clickable((By.ID, "dropdownRadioButton"))
    )
    btn_fecha.click()
    time.sleep(0.5)

    # 2) Esperar a que el dropdown deje de estar oculto
    wait.until(
        EC.visibility_of_element_located((By.ID, "dropdownRadio"))
    )

    # 3) Ahora sí podemos seleccionar “Últimos 7 días”
    radio_7dias = wait.until(
        EC.element_to_be_clickable((By.ID, "filter-radio-example-2"))
    )
    radio_7dias.click()
    time.sleep(1)

    # 4) Aplicar filtros
    btn_buscar = wait.until(
        EC.element_to_be_clickable((By.CSS_SELECTOR,
        "button[data-tooltip-target='tooltip-aplicar-filtros']"))
    )
    btn_buscar.click()

    aplicar_busqueda(driver, wait)
    scroll_to_element(driver)
    # ===============================
    #   FILTRO 2 — Tipo de incidencia
    # ===============================
    print("📌 Filtro 2 → Problemas con baños")

    # 1️⃣ Click en el campo de búsqueda para ABRIR dropdown
    campo_tipo = wait.until(
        EC.element_to_be_clickable((By.ID, "search-tipoIncidencia"))
    )
    driver.execute_script("arguments[0].scrollIntoView(true);", campo_tipo)
    campo_tipo.click()
    time.sleep(0.5)

    # 2️⃣ Esperar a que el dropdown se muestre
    dropdown = wait.until(
        EC.visibility_of_element_located((By.ID, "dropdown-tipoIncidencia"))
    )

    # 3️⃣ Seleccionar la opción
    opcion_banos = wait.until(
        EC.element_to_be_clickable((By.XPATH, "//ul[@id='dropdown-tipoIncidencia']/li[contains(normalize-space(), 'Problemas con baños')]"))
    )

    driver.execute_script("arguments[0].scrollIntoView(true);", opcion_banos)
    opcion_banos.click()
    time.sleep(1)

    # 4️⃣ Aplicar filtros
    btn_buscar = wait.until(
        EC.element_to_be_clickable((By.CSS_SELECTOR,
        "button[data-tooltip-target='tooltip-aplicar-filtros']"))
    )
    btn_buscar.click()
    time.sleep(1)

    print("✔ Tipo de incidencia seleccionado correctamente")

    aplicar_busqueda(driver, wait)
    scroll_to_element(driver)

    # ===============================
    #   FILTRO 3 — Estado
    # ===============================
    print("📌 Filtro 3 → Estado ASIGNADO")

    select_estado = wait.until(EC.element_to_be_clickable((By.ID, "estado")))
    sel = Select(select_estado)
    sel.select_by_visible_text("ASIGNADO")
    time.sleep(1)

    aplicar_busqueda(driver, wait)
    scroll_to_element(driver)

    print("🎉 Todos los filtros aplicados correctamente")

    time.sleep(5)

finally:
    print("Cerrando navegador…")
    driver.quit()
