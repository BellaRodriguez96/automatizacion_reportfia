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
    """Ejecuta la busqueda del listado."""
    btn_buscar = wait.until(EC.element_to_be_clickable((
        By.CSS_SELECTOR,
        "button[data-tooltip-target='tooltip-aplicar-filtros']"
    )))

    driver.execute_script("arguments[0].scrollIntoView(false);", btn_buscar)
    time.sleep(0.2)

    try:
        btn_buscar.click()
        print(" Busqueda ejecutada con click normal")
    except:
        print(" Click interceptado, usando JavaScript")
        driver.execute_script("arguments[0].click();", btn_buscar)

    print(" Busqueda ejecutada correctamente")
    time.sleep(1)   # <-- diferencias de 1 segundo entre filtros


# ======================
#  EJECUCION PRINCIPAL
# ======================

driver = make_driver()
wait = WebDriverWait(driver, 15)

try:
    print(" INICIANDO PRUEBA FUN-38 - Filtrado de reportes")
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
        print(" Sesion ya iniciada, saltando login...")

    # NAVEGAR A REPORTES
    print(" Abriendo menu Reportes...")
    wait.until(EC.element_to_be_clickable((
        By.CSS_SELECTOR,
        "button[data-collapse-toggle='reportes-dropdown']"
    ))).click()

    time.sleep(0.5)
    print(" Menu Reportes desplegado")

    wait.until(EC.element_to_be_clickable((
        By.CSS_SELECTOR,
        "a[href='/reportes/listado-general'], a[href='https://reportfia.deras.dev/reportes/listado-general']"
    ))).click()

    print(" Navegado a Reportes  Listado General")
    time.sleep(0.8)
    
    # ===============================
    #   FILTRO 1  Ultimos 7 dias
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

    # 3) Ahora si podemos seleccionar Ultimos 7 dias
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
    # ===============================
    #   FILTRO 2  Tipo de incidencia
    # ===============================
    print(" Filtro 2  Problemas con baños")

    driver.execute_script("window.scrollTo(0, 0);")
    time.sleep(0.3)

    # 1 Click en el campo de busqueda para ABRIR dropdown
    campo_tipo = wait.until(
        EC.element_to_be_clickable((By.ID, "search-tipoIncidencia"))
    )
    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", campo_tipo)
    try:
        campo_tipo.click()
    except:
        driver.execute_script("arguments[0].click();", campo_tipo)
    time.sleep(0.5)

    # 2 Esperar a que el dropdown se muestre
    wait.until(EC.visibility_of_element_located((By.ID, "dropdown-tipoIncidencia")))

    campo_tipo.clear()
    campo_tipo.send_keys("Problemas con baños")
    time.sleep(0.5)

    # 3 Seleccionar la opcion
    opciones_visibles = wait.until(
        EC.presence_of_all_elements_located((By.CSS_SELECTOR, "#dropdown-tipoIncidencia li"))
    )

    opcion_banos = None
    for opcion in opciones_visibles:
        texto = opcion.text.strip().lower()
        if "banos" in texto or "baños" in texto:
            opcion_banos = opcion
            break

    if opcion_banos is None and opciones_visibles:
        opcion_banos = opciones_visibles[0]

    if opcion_banos is None:
        raise TimeoutException("No se encontraron opciones en el dropdown de tipo de incidencia.")

    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", opcion_banos)
    try:
        opcion_banos.click()
    except:
        driver.execute_script("arguments[0].click();", opcion_banos)
    time.sleep(1)

    # 4 Aplicar filtros
    btn_buscar = wait.until(
        EC.element_to_be_clickable((By.CSS_SELECTOR,
        "button[data-tooltip-target='tooltip-aplicar-filtros']"))
    )
    btn_buscar.click()
    time.sleep(1)

    print(" Tipo de incidencia seleccionado correctamente")

    aplicar_busqueda(driver, wait)

    # ===============================
    #   FILTRO 3  Estado
    # ===============================
    print(" Filtro 3  Estado ASIGNADO")

    select_estado = wait.until(EC.element_to_be_clickable((By.ID, "estado")))
    sel = Select(select_estado)
    sel.select_by_visible_text("ASIGNADO")
    time.sleep(1)

    aplicar_busqueda(driver, wait)

    print(" Todos los filtros aplicados correctamente")

    time.sleep(5)

finally:
    print("Cerrando navegador...")
    driver.quit()
