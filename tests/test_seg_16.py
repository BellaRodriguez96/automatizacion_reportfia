from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time, os, shutil
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager

#  VARIABLES GLOBALES
BASE_URL = "https://reportfia.deras.dev/iniciar-sesion"
USER_CARNET = "aa11001"

CHROME_PROFILE_DIR = os.path.abspath("./.chrome-profile-reportfia")
CHROME_SUBPROFILE  = "ReportFIAProfile"

PASSWORDS_INVALIDAS = ["admin123", "1234", "pass123", None, "", "     ", "password", "letmein", "qwerty", "12345678"]


def make_clean_driver():
    print(" Eliminando perfil persistente anterior...")
    shutil.rmtree(CHROME_PROFILE_DIR, ignore_errors=True)

    print("Creando Chrome limpio...")
    options = webdriver.ChromeOptions()
    options.add_argument(f"--user-data-dir={CHROME_PROFILE_DIR}")
    options.add_argument(f"--profile-directory={CHROME_SUBPROFILE}")
    options.add_argument("--start-maximized")
    # options.add_argument("--headless=new")
    return webdriver.Chrome(
        service=ChromeService(ChromeDriverManager().install()),
        options=options
    )


# --------------------------------------------------------
#   FUNCION: DETECTAR ERROR 500
# --------------------------------------------------------
def detecta_error_500(driver):
    html = driver.page_source.lower()
    # Detecta por contenido tipico
    if "500 internal server error" in html:
        return True
    if "ha ocurrido un error inesperado" in html:
        return True
    if "por favor vuelve a intentarlo mas tarde" in html:
        return True
    return False


# --------------------------------------------------------
#   EJECUCION PRINCIPAL
# --------------------------------------------------------
driver = make_clean_driver()
wait = WebDriverWait(driver, 10)

try:
    print("\n INICIANDO PRUEBA SEG-16 - Inicio de sesion con credenciales predeterminadas/debiles o en blanco")

    prueba_fallida = False

    for pwd in PASSWORDS_INVALIDAS:
        print(f"\n Probando contrasena invalida: {pwd}")

        driver.get(BASE_URL)

        # Detecta error 500 APENAS carga la pantalla
        if detecta_error_500(driver):
            print(" ERROR 500 DETECTADO AL CARGAR EL LOGIN. PRUEBA FALLIDA.")
            prueba_fallida = True
            break

        # Campos login
        input_user = wait.until(EC.presence_of_element_located((By.ID, "carnet")))
        input_pass = wait.until(EC.presence_of_element_located((By.ID, "password")))

        input_user.clear()
        input_pass.clear()
        input_user.send_keys(USER_CARNET)
        input_pass.send_keys(pwd)

        # Click en boton
        btn_login = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
        btn_login.click()

        time.sleep(1)

        #  Detectar si se muestra pantalla 500
        if detecta_error_500(driver):
            print(" ERROR 500 DETECTADO TRAS HACER LOGIN. PRUEBA FALLIDA.")
            prueba_fallida = True
            break

        # Buscar el mensaje de error normal
        try:
            error_login = WebDriverWait(driver, 3).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div.notyf__message"))
            )
            print(f" Correcto: contrasena '{pwd}' fue rechazada  {error_login.text}")

        except:
            print(f" ERROR GRAVE: La contrasena '{pwd}' PERMITIO el acceso.")
            prueba_fallida = True
            break

    # ----------------------------------------
    #   RESULTADO FINAL
    # ----------------------------------------
    print("\n=============================")
    if prueba_fallida:
        print(" PRUEBA FALLIDA")
    else:
        print(" PRUEBA EXITOSA")
    print("=============================")

finally:
    print("Cerrando navegador...")
    driver.quit()
