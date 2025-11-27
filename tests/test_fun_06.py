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
#  UTILIDADES GENERALES
# ======================

def make_driver():
    """Inicia Chrome con perfil persistente para evitar 2FA."""
    options = webdriver.ChromeOptions()
    options.add_argument(f"--user-data-dir={CHROME_PROFILE_DIR}")
    options.add_argument(f"--profile-directory={CHROME_SUBPROFILE}")
    options.add_argument("--start-maximized")
    return webdriver.Chrome(options=options)

def generar_nombre():
    nombres = ["Luis", "Ana", "Carlos", "María", "Fernanda", "José", "Diana", "Ricardo", "Valeria", "Héctor"]
    apellidos = ["González", "Ramírez", "Hernández", "López", "Flores", "Martínez", "Castro", "Morales", "Vargas"]
    return random.choice(nombres), random.choice(apellidos)

def generar_fecha_nacimiento():
    inicio, fin = datetime(1990, 1, 1), datetime(2005, 12, 31)
    fecha = inicio + timedelta(days=random.randrange((fin - inicio).days))
    return fecha.strftime("%d/%m/%Y")

def generar_telefono():
    return f"7{random.randint(1000000, 9999999)}"

def generar_carnet():
    letras = ''.join(random.choice(string.ascii_uppercase) for _ in range(2))
    anio = random.randint(50, 60)
    numero = random.randint(800, 999)
    return f"{letras}{anio:02d}{numero:03d}"

def generar_correo(carnet):
    return f"{carnet}@ues.edu.sv"


# ======================
#  EJECUCIÓN PRINCIPAL
# ======================

driver = make_driver()
wait = WebDriverWait(driver, 15)

try:
    print("🚀 INICIANDO PRUEBA FUN-06 - Registro de usuarios como estudiante")
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

    # NAVEGAR: Seguridad → Usuarios
    print("📂 Abriendo menú Seguridad...")
    wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button[data-collapse-toggle='seguridad-dropdown']"))).click()
    time.sleep(0.5)

    print("✔ Menú Seguridad desplegado")
    wait.until(EC.element_to_be_clickable((
        By.CSS_SELECTOR,
        "a[href='/seguridad/usuarios'], a[href='https://reportfia.deras.dev/seguridad/usuarios']"
    ))).click()

    print("✔ Navegado a Seguridad → Usuarios")
    time.sleep(0.5)

    wait.until(EC.element_to_be_clickable((By.ID, "add-button"))).click()
    time.sleep(0.5)

    # ========= GENERAR DATOS =========
    nombre, apellido = generar_nombre()
    fecha_nac = generar_fecha_nacimiento()
    telefono = generar_telefono()
    carnet = generar_carnet()
    correo = generar_correo(carnet)

    print("🧪 Datos generados:")
    print(nombre, apellido, fecha_nac, telefono, correo, carnet)

    # ========= LLENAR FORMULARIO =========
    wait.until(EC.presence_of_element_located((By.NAME, "nombre"))).send_keys(nombre)
    time.sleep(0.2)
    wait.until(EC.presence_of_element_located((By.NAME, "apellido"))).send_keys(apellido)
    time.sleep(0.2)

    fecha_input = wait.until(EC.element_to_be_clickable((By.NAME, "fecha_nacimiento")))
    driver.execute_script("arguments[0].value = arguments[1];", fecha_input, fecha_nac)
    time.sleep(0.2)

    wait.until(EC.presence_of_element_located((By.NAME, "telefono"))).send_keys(telefono)
    time.sleep(0.2)
    wait.until(EC.presence_of_element_located((By.NAME, "email"))).send_keys(correo)
    time.sleep(0.2)

    campo_carnet = wait.until(EC.element_to_be_clickable((By.ID, "carnet")))
    driver.execute_script("arguments[0].value='';", campo_carnet)
    campo_carnet.send_keys(carnet)
    time.sleep(0.2)

    # Tipo usuario
    tipo_select = wait.until(EC.element_to_be_clickable((By.NAME, "tipo_user")))
    tipo_select.find_element(By.XPATH, "//option[contains(., 'Estudiante')]").click()
    time.sleep(0.2)

    # Escuela
    select = Select(wait.until(EC.element_to_be_clickable((By.ID, "escuela"))))
    select.select_by_value("3")
    time.sleep(0.2)

    # Activo
    checkbox = wait.until(EC.element_to_be_clickable((By.XPATH, "//input[@type='checkbox']")))
    if not checkbox.is_selected():
        checkbox.click()
    time.sleep(0.2)

    print("🎉 FORMULARIO ENVIADO CON ÉXITO")

    # Guardar
    wait.until(EC.element_to_be_clickable((By.ID, "guardar"))).click()
    time.sleep(2)

    # Notificación
    try:
        notyf = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.notyf__message")))
        print("✔ Notificación:", notyf.text)
    except:
        print("⚠ No apareció notificación, continuando…")

    wait.until(EC.url_contains("/seguridad/usuarios"))
    print("✔ Regresó a Gestión de Usuarios")

    # ========= BUSCAR EL USUARIO =========
    print("🔎 Buscando el usuario recién creado...")

    filtro = wait.until(EC.element_to_be_clickable((By.ID, "email-filter")))
    driver.execute_script("arguments[0].value='';", filtro)
    filtro.send_keys(correo)
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
