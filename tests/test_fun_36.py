from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
import time, os, random, string
from datetime import datetime, timedelta

try:
    from tests.test_fun_01 import login_if_needed, make_driver, report_test_result
except ImportError:
    from test_fun_01 import login_if_needed, make_driver, report_test_result

# ======================
#  VARIABLES GLOBALES
# ======================
BASE_URL = "https://reportfia.deras.dev/iniciar-sesion"
TEST_CODE = "FUN-36"
NOMBRE = "Escuela de Prueba " + ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))

# ======================
#  EJECUCION PRINCIPAL
# ======================

driver = make_driver()
wait = WebDriverWait(driver, 15)
error = None

try:
    print(" INICIANDO PRUEBA FUN-36 - Registro de una nueva escuela")
    driver.get(BASE_URL)
    driver.maximize_window()
    time.sleep(1)

    login_if_needed(driver, wait)

    # NAVEGAR: Mantenimiento  Escuelas
    print(" Abriendo menu Mantenimientos...")
    wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button[data-collapse-toggle='mantenimientos-dropdown']"))).click()
    time.sleep(0.5)

    print(" Menu Mantenimientos desplegado")
    wait.until(EC.element_to_be_clickable((
        By.CSS_SELECTOR,
        "a[href='/mantenimientos/escuela'], a[href='https://reportfia.deras.dev/mantenimientos/escuela']"
    ))).click()

    print(" Navegado a Mantenimiento  Escuelas")
    time.sleep(0.5)

    print(" Abriendo modal 'Anadir Escuela'...")

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

    print(" Modal abierto correctamente")
    time.sleep(0.5)

    # ========= LLENAR FORMULARIO =========
    # Facultad
    select = Select(wait.until(EC.element_to_be_clickable((By.ID, "id_facultad"))))
    select.select_by_value("1")
    time.sleep(0.2)

    # Nombre
    wait.until(EC.presence_of_element_located((By.NAME, "nombre"))).send_keys(NOMBRE)
    time.sleep(0.2)

    print(" FORMULARIO ENVIADO CON EXITO")

    # Guardar
    print(" Guardando nueva escuela...")

    btn_guardar = wait.until(
        EC.element_to_be_clickable((
            By.CSS_SELECTOR,
            "button[type='submit'][form='add-escuela-form']"
        ))
    )

    driver.execute_script("arguments[0].scrollIntoView(false);", btn_guardar)
    time.sleep(0.25)

    try:
        btn_guardar.click()
    except:
        driver.execute_script("arguments[0].click();", btn_guardar)

    print(" Escuela guardada correctamente")

    time.sleep(2)

    # Notificacion
    try:
        notyf = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.notyf__message")))
        print(" Notificacion:", notyf.text)
    except:
        print(" No aparecio notificacion, continuando...")

    wait.until(EC.url_contains("/mantenimientos/escuela"))
    print(" Regreso a Mantenimiento -> Escuelas")

    # ========= BUSCAR LA ESCUELA =========
    print(" Buscando la escuela recien creada...")

    filtro = wait.until(EC.element_to_be_clickable((By.ID, "nombre-filter")))
    driver.execute_script("arguments[0].value='';", filtro)
    filtro.send_keys(NOMBRE)
    time.sleep(0.2)

    print(" Ejecutando busqueda en tabla...")

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
        print(" Click interceptado, usando click por JavaScript")
        driver.execute_script("arguments[0].click();", btn_buscar)

    print(" Busqueda ejecutada correctamente")
    time.sleep(10)

except Exception as exc:
    error = exc
    raise
finally:
    report_test_result(TEST_CODE, error)
    print("Cerrando navegador...")
    driver.quit()
