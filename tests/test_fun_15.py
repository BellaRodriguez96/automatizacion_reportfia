# -*- coding: utf-8 -*-
from time import sleep
from datetime import datetime
import os

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

# ========= CONFIG =========
LOGIN_URL    = "https://reportfia.deras.dev/iniciar-sesion"
CREAR_USUARIO_URL = "https://reportfia.deras.dev/seguridad/usuarios/crear"

CRED_USUARIO = "AA11001"
CRED_PASS    = "pass123"

# Carpeta donde se guarda el perfil de Chrome (cookies, “dispositivo de confianza”, etc.)
CHROME_PROFILE_DIR = os.path.abspath("./chrome-profile-reportfia")
# =========================

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

def new_driver():
    """Chrome con perfil PERSISTENTE (mismo 'dispositivo' entre corridas)."""
    log(f"Creando Chrome con perfil persistente en: {CHROME_PROFILE_DIR}")
    opts = webdriver.ChromeOptions()
    opts.add_argument("--start-maximized")
    opts.page_load_strategy = "normal"
    opts.add_argument(f"--user-data-dir={CHROME_PROFILE_DIR}")  # ⚠️ clave para recordar el dispositivo
    # opts.add_argument("--headless=new")  # si quieres sin ventana
    return webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=opts)

def wait_loader(driver, timeout=15):
    try:
        WebDriverWait(driver, timeout).until(
            EC.any_of(
                EC.invisibility_of_element_located((By.ID, "loader")),
                EC.visibility_of_any_elements_located((By.TAG_NAME, "body"))
            )
        )
    except Exception:
        pass

def is_logged_in(driver, timeout=8):
    try:
        WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located(
                (By.XPATH, "//nav[contains(@class,'fixed') and contains(@class,'z-50')]")
            )
        )
        return True
    except TimeoutException:
        return False

def screenshot(driver, name="debug"):
    ruta = os.path.abspath(f"./{name}_{datetime.now().strftime('%H%M%S')}.png")
    try:
        driver.save_screenshot(ruta)
        log(f"📸 Screenshot: {ruta}")
    except Exception:
        pass

def manejar_2fa(driver):
    """
    Maneja TODO el 2FA:
      1. Clic en 'Enviar código' si aparece.
      2. Si NO aparece ni pantalla de 2FA -> asumimos que no se requiere (dispositivo ya confiable).
      3. Si aparece 'Doble factor de autenticación':
         - Leer código desde consola.
         - Rellenar cajitas.
         - Clic en 'Verificar'.
    En futuras corridas, si el servidor ya confía en el dispositivo, no saldrá esta pantalla.
    """
    log("Revisando flujo de 2FA…")

    # 1) Clic en "Enviar código" si aparece
    try:
        btn_enviar = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable(
                (By.XPATH, "//button[contains(normalize-space(),'Enviar código')]")
            )
        )
        log("Clic en 'Enviar código'…")
        btn_enviar.click()
        wait_loader(driver)
    except TimeoutException:
        log("No se encontró 'Enviar código'. Puede que ya se haya enviado o que no haya 2FA.")

    # 2) Verificar si estamos en "Doble factor de autenticación"
    try:
        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located(
                (By.XPATH, "//h1[contains(normalize-space(),'Doble factor de autenticación')]")
            )
        )
        log("Pantalla de 2FA detectada.")
    except TimeoutException:
        log("No se detectó pantalla de 2FA. Asumimos que NO se requiere (dispositivo ya confiable).")
        return

    # 3) Formulario de confirmar código (no el de reenviar)
    try:
        form_2fa = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located(
                (By.XPATH, "//form[@id='otp-form' and contains(@action,'two-factor/confirmar')]")
            )
        )
    except TimeoutException:
        screenshot(driver, "sin_form_2fa")
        raise TimeoutException("No se encontró el formulario de confirmación de 2FA.")

    inputs = form_2fa.find_elements(By.CSS_SELECTOR, "input[type='text']")
    if not inputs:
        screenshot(driver, "sin_inputs_2fa")
        raise TimeoutException("No se encontraron las cajitas de dígitos del 2FA.")

    n = len(inputs)
    log(f"Se encontraron {n} casillas de código.")

    # 4) Pedir código en consola
    while True:
        otp_raw = input(f"Ingrese el código de verificación de {n} dígitos: ").strip()
        otp = "".join(ch for ch in otp_raw if ch.isdigit())
        if len(otp) == n:
            break
        print(f"El código debe tener exactamente {n} dígitos numéricos. Intente de nuevo.")

    log(f"Código 2FA ingresado: {otp}")

    # 5) Rellenar las cajitas
    for inp, d in zip(inputs, otp):
        inp.clear()
        inp.send_keys(d)

    # 6) Clic en "Verificar"
    try:
        btn_verificar = form_2fa.find_element(
            By.XPATH, ".//button[@type='submit' and contains(normalize-space(),'Verificar')]"
        )
        log("Clic en 'Verificar'…")
        btn_verificar.click()
    except Exception:
        screenshot(driver, "sin_boton_verificar_2fa")
        raise TimeoutException("No se encontró el botón 'Verificar' en el formulario 2FA.")

    wait_loader(driver)

    if not is_logged_in(driver):
        screenshot(driver, "no_navbar_despues_2fa")
        raise TimeoutException("Tras 2FA no se detectó el navbar.")

    log("✅ 2FA completado y sesión iniciada.")

def iniciar_sesion(driver, usuario, password):
    log("Abriendo página de login…")
    driver.get(LOGIN_URL)
    wait_loader(driver)

    # Si ya está logueado por sesión previa, puedes decidir:
    # - O dejarlo así
    # - O hacer logout y volver a loguear
    # Aquí validamos solo si YA está logueado:
    if is_logged_in(driver, timeout=3):
        log("Ya se detecta sesión iniciada (navbar presente). No se reingresan credenciales.")
        return

    # Campos de login
    try:
        carnet = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.ID, "carnet"))
        )
        clave = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.ID, "password"))
        )
    except TimeoutException:
        screenshot(driver, "sin_campos_login")
        raise TimeoutException("No se encontraron campos de login.")

    carnet.clear(); carnet.send_keys(usuario)
    clave.clear();  clave.send_keys(password)

    # Recordarme (si existe)
    try:
        remember = driver.find_element(By.ID, "remember_me")
        if not remember.is_selected():
            remember.click()
    except Exception:
        pass

    # Botón "Iniciar sesión"
    try:
        btn_login = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable(
                (By.XPATH, "//button[normalize-space()='Iniciar sesión' and @type='submit']")
            )
        )
        log("Clic en 'Iniciar sesión'…")
        btn_login.click()
    except TimeoutException:
        screenshot(driver, "sin_boton_login")
        raise TimeoutException("No se encontró el botón 'Iniciar sesión'.")

    wait_loader(driver)

    # 2FA si aplica (primera(s) vez/veces)
    manejar_2fa(driver)

    # Validar navbar (logueado)
    if not is_logged_in(driver):
        screenshot(driver, "no_navbar_final")
        raise TimeoutException("No se detectó navbar tras el login.")

    log("✅ Sesión iniciada correctamente.")


# ========== NUEVA PRUEBA: CREAR USUARIO TIPO EMPLEADO ==========
def crear_usuario_empleado(driver):
    """
    Flujo:
      - Navegar a /seguridad/usuarios/crear
      - Completar formulario para usuario EMPLEADO
      - Asignar un rol (EMPLEADO)
      - Guardar y verificar redirección / mensaje
    """
    log("🔹 Iniciando prueba: Crear usuario de tipo EMPLEADO…")

    # 1) Navegar a la página de creación de usuario
    driver.get(CREAR_USUARIO_URL)
    wait_loader(driver)

    wait = WebDriverWait(driver, 15)

    try:
        wait.until(
            EC.visibility_of_element_located(
                (By.XPATH, "//div[contains(@class,'text-2xl') and contains(.,'Gestión de usuarios')]")
            )
        )
        log("Pantalla de 'Gestión de usuarios' cargada correctamente.")
    except TimeoutException:
        screenshot(driver, "no_gestion_usuarios")
        raise TimeoutException("No se encontró el encabezado de 'Gestión de usuarios'.")

    # 2) Generar datos de prueba (correo y carnet únicos)
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    nombre   = "Empleado QA"
    apellido = "Automatizado"
    fecha_nacimiento = "01/01/1990"
    telefono = "2222-3333"
    email    = f"qa.empleado{timestamp}@yopmail.com"
    carnet   = f"QAE{timestamp[-6:]}"  # solo letras/números, <= 20 caracteres

    log(f"Datos de prueba - Nombre: {nombre} {apellido}, Email: {email}, Carnet: {carnet}")

    # 3) Completar campos básicos
    campo_nombre = wait.until(EC.element_to_be_clickable((By.ID, "nombre")))
    campo_apellido = wait.until(EC.element_to_be_clickable((By.ID, "apellido")))
    campo_email = wait.until(EC.element_to_be_clickable((By.ID, "email")))
    campo_carnet = wait.until(EC.element_to_be_clickable((By.ID, "carnet")))

    campo_nombre.clear(); campo_nombre.send_keys(nombre)
    campo_apellido.clear(); campo_apellido.send_keys(apellido)
    campo_email.clear(); campo_email.send_keys(email)
    campo_carnet.clear(); campo_carnet.send_keys(carnet)

    # Fecha de nacimiento (input readonly con datepicker)
    try:
        fecha_input = driver.find_element(By.NAME, "fecha_nacimiento")
        driver.execute_script("arguments[0].removeAttribute('readonly');", fecha_input)
        fecha_input.clear()
        fecha_input.send_keys(fecha_nacimiento)  # formato dd/mm/yyyy
        log("Fecha de nacimiento ingresada.")
    except Exception:
        log("⚠️ No se pudo establecer la fecha de nacimiento (se deja vacío).")

    # Teléfono (opcional pero lo llenamos)
    try:
        campo_tel = driver.find_element(By.ID, "telefono")
        campo_tel.clear()
        campo_tel.send_keys(telefono)
    except Exception:
        log("⚠️ No se pudo llenar el teléfono (campo no encontrado).")

    # 4) Tipo usuario = Empleado (valor '0')
    try:
        select_tipo = driver.find_element(By.ID, "tipo_user")
        select_tipo.click()
        opcion_emp = select_tipo.find_element(By.XPATH, ".//option[@value='0']")
        opcion_emp.click()
        log("Tipo de usuario seleccionado: Empleado.")
        sleep(1)  # permitir que JS muestre fieldGroupEmp
    except Exception:
        log("⚠️ No se pudo seleccionar Tipo de usuario Empleado (se asume ya seleccionado).")

    # 5) Campos específicos de Empleado: Entidad + Puesto
    try:
        entidad_select = driver.find_element(By.ID, "entidad")
        entidad_select.click()
        # Por ejemplo, seleccionar DECANATO (value="1")
        entidad_option = entidad_select.find_element(By.XPATH, ".//option[@value='1']")
        entidad_option.click()
        log("Entidad seleccionada: value=1 (DECANATO).")
        sleep(1)  # dejar que JS cargue los puestos

        puesto_select = driver.find_element(By.ID, "puesto")
        puesto_select.click()
        # Para DECANATO usamos el puesto con value="1" (DECANO) o cualquier otro disponible
        try:
            puesto_option = puesto_select.find_element(By.XPATH, ".//option[@value='1']")
        except Exception:
            # Si por alguna razón no existe value=1, tomar el primer option distinto de vacío
            puesto_option = puesto_select.find_element(By.XPATH, ".//option[@value!='']")
        puesto_option.click()
        log(f"Puesto seleccionado: {puesto_option.text.strip()}")
    except Exception:
        screenshot(driver, "error_entidad_puesto")
        raise TimeoutException("No se pudo seleccionar entidad/puesto para el empleado.")

    # 6) Asignar al menos un rol (usaremos el rol 'EMPLEADO')
    try:
        available_roles = driver.find_element(By.CSS_SELECTOR, "ul.available-items")
        rol_empleado = available_roles.find_element(
            By.XPATH, ".//li[@data-item-name='EMPLEADO']"
        )
        rol_empleado.click()
        log("Rol 'EMPLEADO' seleccionado en lista disponible.")

        boton_add = driver.find_element(By.CSS_SELECTOR, "button.add-item")
        boton_add.click()
        log("Rol 'EMPLEADO' movido a 'Roles asignados'.")
        sleep(1)
    except Exception:
        screenshot(driver, "error_roles_empleado")
        raise TimeoutException("No se pudo asignar el rol EMPLEADO al usuario.")

    # 7) Guardar Cambios
    try:
        btn_guardar = driver.find_element(By.ID, "guardar")
        log("Haciendo clic en 'Guardar Cambios'…")
        btn_guardar.click()
    except Exception:
        screenshot(driver, "error_click_guardar")
        raise TimeoutException("No se pudo hacer clic en el botón 'Guardar Cambios'.")

    wait_loader(driver, timeout=20)
    sleep(3)

    # 8) Verificar resultado
    #   a) Preferencia: redirección al listado de usuarios
    exito = False
    try:
        WebDriverWait(driver, 10).until(
            EC.url_contains("/seguridad/usuarios")
        )
        if "/seguridad/usuarios" in driver.current_url and "/crear" not in driver.current_url:
            exito = True
    except TimeoutException:
        exito = False

    #   b) Intentar leer mensaje de notificación (notyf-announcer)
    try:
        announcer = driver.find_element(By.CLASS_NAME, "notyf-announcer")
        texto_noty = announcer.text.strip()
        if texto_noty:
            log(f"Mensaje notificación (Notyf): {texto_noty}")
    except Exception:
        pass

    if exito:
        log("✅ Usuario EMPLEADO creado correctamente (redirección al listado de usuarios detectada).")
        log(f"   ➤ Email creado: {email}")
        log(f"   ➤ Usuario/Carnet creado: {carnet}")
    else:
        log("⚠️ No se detectó redirección al listado de usuarios después de guardar.")
        log("   Es posible que haya validaciones del lado servidor (por ejemplo, email/carnet duplicado).")
        screenshot(driver, "crear_usuario_empleado_fallido")


# ============================ MAIN ============================
if __name__ == "__main__":
    driver = new_driver()
    try:
        iniciar_sesion(driver, CRED_USUARIO, CRED_PASS)
        log("🔵 Sesión autenticada, iniciando prueba de creación de usuario EMPLEADO…")
        crear_usuario_empleado(driver)
        sleep(5)
    except Exception as e:
        log(f"❌ Error en el flujo: {e}")
        screenshot(driver, "error_general_crear_usuario")
        raise
    finally:
        driver.quit()
