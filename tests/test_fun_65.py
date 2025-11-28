from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time, os, random, string, base64

# ======================
#  CONFIGURACION GLOBAL
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


def crear_imagen_prueba():
    """Genera un PNG pequeno para subir como comprobante."""
    img_data = base64.b64decode(
        b'iVBORw0KGgoAAAANSUhEUgAAAAoAAAAKCAYAAACNMs+9AAAAHElEQVQoU2NkgIAgFo2BgYGB4T8mBgwGJQwMAE2YCxY3E8VgAAAAAElFTkSuQmCC'
    )
    ruta = os.path.abspath("imagen_prueba.png")
    with open(ruta, "wb") as f:
        f.write(img_data)
    return ruta


def generar_texto_aleatorio(base, longitud=6):
    sufijo = ''.join(random.choices(string.ascii_uppercase + string.digits, k=longitud))
    return f"{base} {sufijo}"


def aplicar_busqueda(driver, wait):
    """Ejecuta click en el boton Aplicar Filtros."""
    btn_buscar = wait.until(EC.element_to_be_clickable((
        By.CSS_SELECTOR,
        "button[data-tooltip-target='tooltip-aplicar-filtros']"
    )))

    driver.execute_script("arguments[0].scrollIntoView(false);", btn_buscar)
    time.sleep(0.25)

    try:
        btn_buscar.click()
    except:
        driver.execute_script("arguments[0].click();", btn_buscar)

    print(" Busqueda ejecutada")
    time.sleep(1)


# ======================
#  INICIO DE PRUEBA
# ======================

driver = make_driver()
wait = WebDriverWait(driver, 15)

try:
    print(" INICIANDO PRUEBA FUN-65 - Registro de reporte nuevo")
    driver.get(BASE_URL)
    time.sleep(1)

    # -----------------------------------------------------
    # LOGIN
    # -----------------------------------------------------
    if URL_INICIO not in driver.current_url:
        input_user = wait.until(EC.presence_of_element_located((By.ID, "carnet")))
        input_pass = wait.until(EC.presence_of_element_located((By.ID, "password")))
        input_user.send_keys(USER_CARNET)
        input_pass.send_keys(USER_PASSWORD)
        driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        time.sleep(1)
    else:
        print(" Sesion ya iniciada")

    # -----------------------------------------------------
    # NAVEGAR A REGISTRO DE REPORTES
    # -----------------------------------------------------
    print(" Abriendo menu Reportes...")

    wait.until(EC.element_to_be_clickable((
        By.CSS_SELECTOR, "button[data-collapse-toggle='reportes-dropdown']"
    ))).click()

    wait.until(EC.element_to_be_clickable((
        By.XPATH, "//a[contains(@href,'/reportes/listado-general')]"
    ))).click()

    wait.until(EC.element_to_be_clickable((
        By.XPATH, "//a[contains(@href,'/reportes/registrar')]"
    ))).click()

    # -----------------------------------------------------
    # SELECCIONAR INCIDENCIA ALEATORIA
    # -----------------------------------------------------
    print(" Seleccionando incidencia...")

    campo_inc = wait.until(EC.element_to_be_clickable((By.ID, "search-id_tipo_incidencia")))
    campo_inc.click()
    time.sleep(0.4)

    # Limpiar y escribir espacio para mostrar todas las opciones
    campo_inc.send_keys(" ")
    time.sleep(0.6)

    # Seleccionar UL real de Flowbite
    ul_menu = wait.until(
        EC.presence_of_element_located((By.XPATH, "//div[contains(@class,'relative')]//ul"))
    )

    li_items = [
        li for li in ul_menu.find_elements(By.TAG_NAME, "li")
        if li.text.strip() != "" and li.is_displayed()
    ]

    if not li_items:
        raise Exception(" No hay incidencias visibles")

    item_random = random.choice(li_items)
    incidencia_texto = item_random.text.strip()

    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", item_random)
    driver.execute_script("arguments[0].click();", item_random)

    print(" Incidencia seleccionada:", incidencia_texto)

    # -----------------------------------------------------
    # DESCRIPCION
    # -----------------------------------------------------
    descripcion_texto = generar_texto_aleatorio("Reporte automatico QA")
    descripcion = wait.until(EC.presence_of_element_located((By.ID, "descripcion")))
    descripcion.send_keys(descripcion_texto)
    print(" Descripcion ingresada:", descripcion_texto)

    # -----------------------------------------------------
    # LUGAR
    # -----------------------------------------------------
    print(" Obteniendo lugares reales del sistema...")

    input_lugar = wait.until(EC.element_to_be_clickable((By.ID, "lugar-input")))
    input_lugar.click()
    input_lugar.send_keys(" ")
    time.sleep(0.6)

    lugares_reales = wait.until(
        EC.presence_of_all_elements_located((By.CSS_SELECTOR, "ul li"))
    )

    lista_lugares = [l.text.strip() for l in lugares_reales if l.text.strip()]
    lugar_random = random.choice(lista_lugares)

    print(" Lugar elegido aleatoriamente:", lugar_random)

    driver.execute_script("arguments[0].value='';", input_lugar)
    input_lugar.send_keys(lugar_random)
    time.sleep(0.4)

    opcion_lugar = wait.until(
        EC.element_to_be_clickable((By.XPATH, f"//li[contains(., '{lugar_random}')]"))
    )
    opcion_lugar.click()

    # -----------------------------------------------------
    # IMAGEN
    # -----------------------------------------------------
    ruta_img = crear_imagen_prueba()
    campo_imagen = wait.until(EC.presence_of_element_located((By.ID, "comprobantes")))
    campo_imagen.send_keys(ruta_img)
    print(" Imagen cargada")

    # -----------------------------------------------------
    # ENVIAR REPORTE
    # -----------------------------------------------------
    print(" Enviando reporte...")

    btn_enviar = wait.until(
        EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Enviar reporte')]"))
    )

    driver.execute_script("arguments[0].click();", btn_enviar)

    btn_confirmar = wait.until(
        EC.element_to_be_clickable((By.XPATH, "//div[@id='send-modal']//button[@type='submit']"))
    )

    driver.execute_script("arguments[0].click();", btn_confirmar)
    print(" Reporte enviado ")

    # Notificacion
    try:
        notyf = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.notyf__message")))
        print(" Notificacion:", notyf.text)
    except:
        print(" No aparecio notificacion")

    # -----------------------------------------------------
    # REGRESAR AL LISTADO
    # -----------------------------------------------------
    print(" Volviendo al listado...")

    try:
        wait.until(EC.url_contains("/reportes/listado-general"))
    except:
        enlace_listado = wait.until(
            EC.element_to_be_clickable((By.XPATH, "//a[contains(@href,'/reportes/listado-general')]"))
        )
        driver.execute_script("arguments[0].click();", enlace_listado)

    print(" Ya estamos en el listado")

    # -----------------------------------------------------
    # APLICAR FILTRO HOY
    # -----------------------------------------------------
    print(" Aplicando filtro HOY...")

    btn_fecha = wait.until(EC.element_to_be_clickable((By.ID, "dropdownRadioButton")))
    btn_fecha.click()

    wait.until(EC.visibility_of_element_located((By.ID, "dropdownRadio")))

    radio_hoy = wait.until(EC.element_to_be_clickable((By.ID, "filter-radio-example-1")))
    radio_hoy.click()

    aplicar_busqueda(driver, wait)

    time.sleep(4)

finally:
    print("Cerrando navegador...")
    driver.quit()
