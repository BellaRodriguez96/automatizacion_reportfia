import os
import re
import shutil
import subprocess
import sys
import time
from contextlib import contextmanager

from selenium import webdriver
from selenium.common.exceptions import TimeoutException, SessionNotCreatedException
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

# ==========================================================
#   VARIABLES GLOBALES
# ==========================================================
BASE_URL = "https://reportfia.deras.dev/iniciar-sesion"
URL_INICIO = "https://reportfia.deras.dev/inicio"
USER_CARNET = "aa11001"
USER_PASSWORD = "pass123"
YOPMAIL_URL = "https://yopmail.com/es/"

# Persistencia del dispositivo (perfil de Chrome)
CHROME_PROFILE_DIR = os.path.abspath("./.chrome-profile-reportfia")
CHROME_SUBPROFILE = "ReportFIAProfile"


def report_test_result(test_code: str, error: Exception | None = None) -> None:
    """Imprime un mensaje estandarizado con el estado del caso."""
    if error is None:
        print(f"[{test_code}] PASSED")
    else:
        print(f"[{test_code}] FAILED: {error}")


def limpiar_perfil_chrome() -> None:
    """Elimina el perfil persistente cuando se requiere un login limpio."""
    if os.path.exists(CHROME_PROFILE_DIR):
        shutil.rmtree(CHROME_PROFILE_DIR, ignore_errors=True)

def cerrar_procesos_chrome() -> None:
    """Intenta cerrar procesos huérfanos de Chrome/ChromeDriver."""
    if not sys.platform.startswith("win"):
        return

    for proc in ("chromedriver.exe", "chrome.exe"):
        try:
            subprocess.run(
                ["taskkill", "/F", "/IM", proc],
                capture_output=True,
                text=True,
                check=False,
            )
        except Exception:
            pass


def make_driver(reset_profile: bool = False) -> webdriver.Chrome:
    """Crea una nueva instancia de Chrome usando el perfil persistente."""
    if reset_profile:
        print("Limpiando perfil persistente antes de forzar el flujo completo...")
        limpiar_perfil_chrome()

    options = webdriver.ChromeOptions()
    options.add_argument(f"--user-data-dir={CHROME_PROFILE_DIR}")
    options.add_argument(f"--profile-directory={CHROME_SUBPROFILE}")
    options.add_argument("--start-maximized")
    options.page_load_strategy = "normal"

    try:
        return webdriver.Chrome(
            service=ChromeService(ChromeDriverManager().install()),
            options=options,
        )
    except SessionNotCreatedException as exc:
        if reset_profile:
            raise
        print("No se pudo iniciar Chrome con el perfil existente. Limpiando y reintentando...")
        cerrar_procesos_chrome()
        limpiar_perfil_chrome()
        return make_driver(reset_profile=True)


def validar_login_exitoso(driver: webdriver.Chrome) -> bool:
    """Verifica que la URL actual sea la de inicio."""
    time.sleep(0.5)
    if URL_INICIO in driver.current_url:
        print("Se llego correctamente al inicio del sistema.")
        return True
    return False


def abrir_yopmail_y_obtener_codigo(
    driver: webdriver.Chrome,
    wait: WebDriverWait,
    carnet: str,
) -> str:
    """Abre Yopmail en otra pestana y obtiene el codigo 2FA."""
    if not driver.window_handles:
        raise RuntimeError("No existe ninguna pestana activa en Chrome.")

    driver.switch_to.window(driver.window_handles[0])
    time.sleep(0.5)
    driver.execute_script("window.open('about:blank', '_blank');")
    time.sleep(0.5)

    nueva_pestana = driver.window_handles[-1]
    driver.switch_to.window(nueva_pestana)
    print("Nueva pestana abierta para Yopmail.")

    driver.get(YOPMAIL_URL)
    if "yopmail.com/es/wm" in driver.current_url or "yopmail.com/es/inbox" in driver.current_url:
        driver.get(YOPMAIL_URL)
        time.sleep(0.5)

    campo = wait.until(EC.presence_of_element_located((By.ID, "login")))
    campo.clear()
    campo.send_keys(carnet)

    campo = wait.until(EC.element_to_be_clickable((By.ID, "login")))
    driver.execute_script("arguments[0].focus();", campo)
    time.sleep(0.2)
    campo.send_keys(Keys.ENTER)
    print("ENTER enviado. Abriendo bandeja...")
    time.sleep(0.5)

    iframes = driver.find_elements(By.TAG_NAME, "iframe")
    iframe_encontrado = False
    for index, iframe in enumerate(iframes):
        name = iframe.get_attribute("name")
        iframe_id = iframe.get_attribute("id")
        if name == "ifmail" or iframe_id == "ifmail":
            driver.switch_to.frame(iframe)
            iframe_encontrado = True
            print(f"Entramos al iframe correcto (index={index}).")
            break

    if not iframe_encontrado:
        raise RuntimeError("No se encontro el iframe del correo (ifmail).")

    time.sleep(0.5)
    codigo = None

    try:
        strong_el = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#mail strong")))
        codigo = strong_el.text.strip()
        print("Codigo encontrado:", codigo)
    except Exception:
        print("Selector #mail strong fallo, buscando codigo con regex...")
        cuerpo = driver.find_element(By.TAG_NAME, "body").text
        match = re.search(r"\b\d{6}\b", cuerpo)
        if match:
            codigo = match.group(0)
            print("Codigo encontrado por regex:", codigo)

    finally:
        driver.switch_to.default_content()

    if not codigo:
        raise RuntimeError("No se pudo encontrar el codigo 2FA en el correo.")

    return codigo


def llenar_2fa(driver: webdriver.Chrome, wait: WebDriverWait, codigo: str) -> None:
    """Llena cada input del 2FA con el codigo recibido."""
    inputs_2fa = wait.until(
        EC.presence_of_all_elements_located((By.CSS_SELECTOR, "input[type='text'][maxlength='1']"))
    )
    for index, digit in enumerate(codigo):
        inputs_2fa[index].send_keys(digit)
        time.sleep(0.1)

    print("Codigo 2FA escrito correctamente.")

    btn_verificar = wait.until(
        EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Verificar')]"))
    )
    btn_verificar.click()


def login_if_needed(
    driver: webdriver.Chrome,
    wait: WebDriverWait,
    base_url: str = BASE_URL,
    user: str = USER_CARNET,
    password: str = USER_PASSWORD,
    auto_2fa: bool = True,
) -> None:
    """
    Realiza login simple (sin 2FA) unicamente si no existe sesion previa.

    Esta funcion es utilizada por otros casos de prueba que solo
    necesitan garantizar una sesion activa usando el perfil persistente.
    """
    if URL_INICIO in driver.current_url:
        print("Sesion ya iniciada, se omite el login manual.")
        return

    if base_url not in driver.current_url:
        driver.get(base_url)

    try:
        input_user = wait.until(EC.presence_of_element_located((By.ID, "carnet")))
        input_pass = wait.until(EC.presence_of_element_located((By.ID, "password")))
    except TimeoutException:
        if validar_login_exitoso(driver):
            print("Sesion ya activa durante login_if_needed.")
            return
        if "two-factor" in driver.current_url:
            if auto_2fa:
                print("Pantalla 2FA detectada antes de ingresar credenciales. Resolviendo...")
                resolver_2fa(driver, wait)
                if validar_login_exitoso(driver):
                    return
                raise RuntimeError("No se completo el login despues de resolver 2FA.")
            raise RuntimeError(
                "Se encontro la pantalla de 2FA antes de ingresar credenciales."
            )
        raise

    input_user.clear()
    input_pass.clear()
    input_user.send_keys(user)
    input_pass.send_keys(password)

    driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
    time.sleep(0.5)

    if "two-factor" in driver.current_url:
        if auto_2fa:
            resolver_2fa(driver, wait)
            if validar_login_exitoso(driver):
                return
            raise RuntimeError("No se completo el login despues del 2FA.")

        raise RuntimeError(
            "Se encontro la pantalla de 2FA. Ejecuta tests/test_fun_01.py para "
            "iniciar sesion y guardar la persistencia antes de correr este caso."
        )

    if not validar_login_exitoso(driver):
        raise RuntimeError("No se pudo iniciar sesion usando las credenciales proporcionadas.")


def ejecutar_login_con_2fa(driver: webdriver.Chrome, wait: WebDriverWait) -> None:
    """Ejecuta el flujo completo del caso FUN-01 (login con posible 2FA)."""
    print("INICIANDO PRUEBA FUN-01 - LOGIN")
    driver.get(BASE_URL)
    driver.maximize_window()

    try:
        input_user = wait.until(EC.presence_of_element_located((By.ID, "carnet")))
        input_pass = wait.until(EC.presence_of_element_located((By.ID, "password")))
    except TimeoutException:
        if validar_login_exitoso(driver):
            print("Sesion ya activa, no es necesario reloguear.")
            return
        if "two-factor" in driver.current_url:
            print("Pantalla 2FA encontrada antes de ingresar credenciales; completando verificacion previa...")
            resolver_2fa(driver, wait)
            if validar_login_exitoso(driver):
                print("Sesion restaurada desde flujo 2FA previo.")
                return
        raise

    input_user.send_keys(USER_CARNET)
    input_pass.send_keys(USER_PASSWORD)

    driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
    time.sleep(0.5)

    try:
        error_login = WebDriverWait(driver, 3).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.notyf__message"))
        )
        raise RuntimeError(f"CASO FALLO: {error_login.text}")
    except TimeoutException:
        print("No hay error de credenciales.")

    if "two-factor" not in driver.current_url:
        if validar_login_exitoso(driver):
            print("Login completado sin requerir 2FA.")
            return
        raise RuntimeError("No hubo error, pero tampoco se llego a /inicio.")

    print("Requiere 2FA. Enviando codigo...")
    resolver_2fa(driver, wait)

    if validar_login_exitoso(driver):
        print("CASO FUN-01 -> PASSED")
        return

    raise RuntimeError("Despues del 2FA NO se llego a /inicio.")


def run_test_fun_01(reset_profile: bool = True) -> None:
    """Permite ejecutar el caso FUN-01 y reutilizarlo desde otros modulos."""
    with start_test_session("FUN-01", reset_profile=reset_profile) as (driver, wait):
        ejecutar_login_con_2fa(driver, wait)


@contextmanager
def start_test_session(test_code: str, *, reset_profile: bool = False):
    """
    Crea un WebDriver con perfil persistente y reporta el resultado del caso.

    Uso:
        with start_test_session("FUN-06") as (driver, wait):
            login_if_needed(driver, wait)
            # ... pasos del caso ...
    """
    driver = make_driver(reset_profile=reset_profile)
    wait = WebDriverWait(driver, 15)
    error: Exception | None = None

    try:
        yield driver, wait
    except Exception as exc:
        error = exc
        raise
    finally:
        report_test_result(test_code, error)
        print("Cerrando navegador...")
        driver.quit()


def resolver_2fa(driver: webdriver.Chrome, wait: WebDriverWait) -> None:
    """Completa el flujo de doble factor reutilizado por otros casos."""
    wait.until(EC.url_contains("two-factor"))

    boton_enviar = None
    selectores_prioritarios = [
        "//form[contains(translate(., 'ÓóÍíÁáÉéÚú', 'OoIiAaEeUu'), 'ENVIAR CODIGO')]//button[@type='submit']",
        "//button[contains(translate(., 'ÓóÍíÁáÉéÚú', 'OoIiAaEeUu'), 'ENVIAR CODIGO')]",
        "//form[contains(@action, 'two-factor')]//button[@type='submit']",
    ]

    for xpath in selectores_prioritarios:
        try:
            boton_enviar = wait.until(EC.element_to_be_clickable((By.XPATH, xpath)))
            break
        except TimeoutException:
            continue

    if not boton_enviar:
        for btn in driver.find_elements(By.XPATH, "//button[@type='submit' or @type='button']"):
            texto = btn.text.strip().lower()
            if "enviar" in texto and "codigo" in texto:
                boton_enviar = btn
                break

    if not boton_enviar:
        raise TimeoutException("No se encontro un boton visible de 'Enviar codigo' en 2FA.")

    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", boton_enviar)
    time.sleep(0.2)

    try:
        boton_enviar.click()
    except Exception:
        driver.execute_script("arguments[0].click();", boton_enviar)

    time.sleep(0.5)
    print("Boton 'Enviar codigo' presionado.")

    main_window = driver.current_window_handle
    codigo = abrir_yopmail_y_obtener_codigo(driver, wait, USER_CARNET)

    driver.switch_to.window(main_window)
    time.sleep(0.5)

    llenar_2fa(driver, wait, codigo)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Ejecuta el caso FUN-01 (login con 2FA).")
    parser.add_argument(
        "--no-reset-profile",
        action="store_true",
        help="No elimina el perfil persistente antes de crear el driver.",
    )
    args = parser.parse_args()
    run_test_fun_01(reset_profile=not args.no_reset_profile)
