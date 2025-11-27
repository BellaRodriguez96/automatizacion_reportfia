from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time, os

# ======================
#  VARIABLES GLOBALES
# ======================
BASE_URL = "https://reportfia.deras.dev/iniciar-sesion"
URL_INICIO = "https://reportfia.deras.dev/inicio"

USER_CARNET = "aa11001"
USER_PASSWORD = "pass123"

# Perfil Chrome (si querés evitar 2FA)
CHROME_PROFILE_DIR = os.path.abspath("./.chrome-profile-reportfia")
CHROME_SUBPROFILE  = "ReportFIAProfile"


def make_driver():
    """Reutiliza el perfil de Chrome para evitar el 2FA."""
    options = webdriver.ChromeOptions()
    options.add_argument(f"--user-data-dir={CHROME_PROFILE_DIR}")
    options.add_argument(f"--profile-directory={CHROME_SUBPROFILE}")
    options.add_argument("--start-maximized")
    return webdriver.Chrome(options=options)


# Iniciar WebDriver con el perfil persistente
driver = make_driver()
wait = WebDriverWait(driver, 15)


try:
    print("🚀 INICIANDO PRUEBA FUN-06 - LOGIN")
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
finally:
    print("Cerrando navegador…")
    driver.quit()
