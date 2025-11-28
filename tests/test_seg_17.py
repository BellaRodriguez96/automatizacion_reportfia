from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time, os, shutil
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager

BASE_URL = "https://reportfia.deras.dev/iniciar-sesion"
USER_CARNET = "aa11001"

CHROME_PROFILE_DIR = os.path.abspath("./.chrome-profile-reportfia")
CHROME_SUBPROFILE  = "ReportFIAProfile"

PASSWORDS_INVALIDAS_BLOQUEO = ["pass1234"] * 10  # 10 intentos


# --------------------------------------------------------
#   DRIVER LIMPIO
# --------------------------------------------------------
def make_clean_driver():
    shutil.rmtree(CHROME_PROFILE_DIR, ignore_errors=True)
    options = webdriver.ChromeOptions()
    options.add_argument(f"--user-data-dir={CHROME_PROFILE_DIR}")
    options.add_argument(f"--profile-directory={CHROME_SUBPROFILE}")
    options.add_argument("--start-maximized")
    return webdriver.Chrome(
        service=ChromeService(ChromeDriverManager().install()),
        options=options
    )


# --------------------------------------------------------
#   DETECTAR ERROR 500
# --------------------------------------------------------
def detecta_error_500(driver):
    html = driver.page_source.lower()
    return (
        "500 internal server error" in html or
        "ha ocurrido un error inesperado" in html or
        "por favor vuelve a intentarlo mas tarde" in html
    )


# --------------------------------------------------------
#   DETECTAR CAPCHA / BLOQUEO
# --------------------------------------------------------
def detecta_bloqueo_o_captcha(driver):
    html = driver.page_source.lower()

    # reCAPTCHA iframe
    if "recaptcha" in html:
        return True

    # Palabras típicas de bloqueo
    palabras = [
        "intentos",
        "bloqueado",
        "demasiados intentos",
        "intentos excedidos",
        "captcha",
        "espera",
        "seguridad"
    ]
    if any(p in html for p in palabras):
        return True

    return False


# --------------------------------------------------------
#   EJECUCIÓN PRINCIPAL
# --------------------------------------------------------
driver = make_clean_driver()
wait = WebDriverWait(driver, 10)

try:
    print("\n🚀 INICIANDO PRUEBA SEG-17 - Fuerza bruta y activación de CAPTCHA")

    prueba_fallida = False
    captcha_activado = False

    for intento, pwd in enumerate(PASSWORDS_INVALIDAS_BLOQUEO, start=1):
        print(f"\n🔎 Intento {intento} con contraseña inválida: {pwd}")

        driver.get(BASE_URL)

        # Error 500 al cargar login
        if detecta_error_500(driver):
            print("❌ ERROR 500 DETECTADO AL CARGAR LOGIN")
            prueba_fallida = True
            break

        # Campos login
        input_user = wait.until(EC.presence_of_element_located((By.ID, "carnet")))
        input_pass = wait.until(EC.presence_of_element_located((By.ID, "password")))

        input_user.clear()
        input_pass.clear()
        input_user.send_keys(USER_CARNET)
        input_pass.send_keys(pwd)

        btn_login = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
        btn_login.click()

        time.sleep(1)

        # Error 500 después del login
        if detecta_error_500(driver):
            print("❌ ERROR 500 DETECTADO DESPUÉS DEL LOGIN")
            prueba_fallida = True
            break

        # Intentar detectar bloqueo o CAPTCHA
        if intento >= 5:
            if detecta_bloqueo_o_captcha(driver):
                print("✔ SISTEMA ACTIVÓ BLOQUEO / CAPTCHA CORRECTAMENTE.")
                captcha_activado = True
                break

        # Error normal de login
        try:
            error_login = WebDriverWait(driver, 2).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div.notyf__message"))
            )
            print(f"✔ Contraseña rechazada: {error_login.text}")
        except:
            print(f"❌ ERROR GRAVE: La contraseña '{pwd}' PERMITIÓ acceso.")
            prueba_fallida = True
            break

    # --------------------------------------------------------
    #   RESULTADO FINAL
    # --------------------------------------------------------
    print("\n=============================")

    if prueba_fallida:
        print("❌ PRUEBA FALLIDA")
    else:
        if not captcha_activado:
            print("❌ PRUEBA FALLIDA: Tras 5 intentos NO se activó bloqueo ni CAPTCHA.")
        else:
            print("🎉 PRUEBA EXITOSA")

    print("=============================")

finally:
    print("Cerrando navegador…")
    driver.quit()
