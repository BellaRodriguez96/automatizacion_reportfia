# tests/test_fun_75_forgot_password.py
# Caso: Validar que al solicitar recuperación con un correo NO registrado el sistema muestre error.
# Uso: pytest -q

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
import time, os

# ---------------- CONFIG ----------------
HOME_URL = "https://reportfia.deras.dev/iniciar-sesion"
OUTPUT_DIR = "selenium_outputs_forgot_password_invalid_email"
os.makedirs(OUTPUT_DIR, exist_ok=True)
TIMEOUT = 12

# correo que asumimos NO está registrado
TEST_EMAIL = "AL180444@ues.edu.sv"


# ---------------- HELPERS ----------------
def screenshot(driver, name):
    path = os.path.join(OUTPUT_DIR, f"{int(time.time()*1000)}_{name}.png")
    try:
        driver.save_screenshot(path)
    except Exception:
        pass
    return path

def detect_error_message(driver):
    """Detecta mensaje de error por correo no registrado en el flujo de 'forgot password'."""
    try:
        body_text = driver.find_element(By.TAG_NAME, "body").get_attribute("innerText").lower()
        # frases esperables en español
        for kw in ("no registrado", "no existe", "correo no registrado", "correo no encontrado", "usuario no encontrado", "no hemos encontrado", "no se encontró"):
            if kw in body_text:
                return True
    except Exception:
        pass

    # toasts / noty / sweetalert comunes
    selectors = [".noty_message", ".noty_bar", ".toast", ".toast-message", ".alert", ".notification", ".noty", ".swal2-popup"]
    for sel in selectors:
        try:
            els = driver.find_elements(By.CSS_SELECTOR, sel)
            for e in els:
                if e.is_displayed() and e.text.strip():
                    txt = e.text.strip().lower()
                    for kw in ("no existe", "no registrado", "no encontrado", "correo"):
                        if kw in txt:
                            return True
        except Exception:
            pass

    return False

# ---------------- TEST ----------------
def test_forgot_password_with_unregistered_email():
    driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()))
    driver.maximize_window()

    try:
        # 1) Abrir home
        driver.get(HOME_URL)
        screenshot(driver, "01_home")

        # 2) Click en "¿Olvidaste tu contraseña?" (link href '/forgot-password' o por texto)
        try:
            link = WebDriverWait(driver, TIMEOUT).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "a[href*='/forgot-password']"))
            )
        except Exception:
            # fallback por texto (insensible a mayúsculas)
            link = WebDriverWait(driver, TIMEOUT).until(
                EC.element_to_be_clickable((By.XPATH,
                    "//a[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'), 'olvidaste tu contraseña') or contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'), 'olvidó contraseña') or contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'), 'forgot password')]"))
            )
        link.click()

        # 3) Esperar página o modal de forgot-password
        # si la app redirige a /forgot-password esperamos la URL; si es modal, los campos aparecerán igualmente
        try:
            WebDriverWait(driver, TIMEOUT).until(EC.url_contains("/forgot-password"))
        except Exception:
            # no hace nada; igual intentamos localizar el campo email en la página/modal
            pass
        screenshot(driver, "02_forgot_page_opened")

        # 4) Localizar input de email (intenta varios selectores comunes)
        email_input = None
        candidates = [
            (By.NAME, "email"),
            (By.ID, "email"),
            (By.CSS_SELECTOR, "input[type='email']"),
            (By.CSS_SELECTOR, "form input[name='email']"),
            (By.CSS_SELECTOR, "form input[type='text']"),
        ]
        for by, sel in candidates:
            try:
                el = WebDriverWait(driver, 2).until(EC.presence_of_element_located((by, sel)))
                if el:
                    email_input = el
                    break
            except Exception:
                continue

        if email_input is None:
            # última oportunidad: buscar cualquier input dentro del form que tenga placeholder con 'email' o 'correo'
            try:
                el = driver.find_element(By.XPATH, "//form//input[contains(translate(@placeholder,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'correo') or contains(translate(@placeholder,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'email')]")
                email_input = el
            except Exception:
                pass

        assert email_input is not None, "No se encontró el input de correo en la pantalla de 'forgot password'. Revisa el selector."

        # 5) Escribir correo NO registrado y enviar
        email_input.clear()
        email_input.send_keys(TEST_EMAIL)
        time.sleep(2)
        screenshot(driver, "03_filled_forgot")

        # Buscar botón submit dentro del form o botón con texto 'Enviar'/'Recuperar'/'Enviar correo'
        submit_btn = None
        try:
            submit_btn = driver.find_element(By.CSS_SELECTOR, "form button[type='submit']")
        except Exception:
            # fallback por texto
            try:
                submit_btn = driver.find_element(By.XPATH,
                    "//form//button[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'), 'enviar') or contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'), 'recuperar') or contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'), 'restablecer') or contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'), 'send')]")
            except Exception:
                pass

        assert submit_btn is not None, "No se encontró el botón de envío en la pantalla de 'forgot password'."

        submit_btn.click()
        # esperar posible respuesta
        time.sleep(2)

        # 6) Detectar mensaje de error
        found = False
        start = time.time()
        timeout_wait = 8
        while time.time() - start < timeout_wait:
            if detect_error_message(driver):
                found = True
                break
            time.sleep(2)

        screenshot(driver, "04_after_submit")

        assert found, (
            "No se detectó mensaje de error indicando que el correo no está registrado. "
            f"Revisá las capturas en {OUTPUT_DIR}"
        )

    finally:
        driver.quit()
