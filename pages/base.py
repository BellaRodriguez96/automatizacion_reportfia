from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

class Base:
    # Clase base para los Page Objects.
    URL = "https://reportfia.deras.dev/"

    """
    Clase Base mejorada:
    - Acepta `driver` opcional en el constructor para permitir crear la
      instancia antes de inicializar el WebDriver (útil en fixtures).
    - `get_driver` ahora asigna `self.driver` y `self._wait`.
    """

    # Constructor que acepta un driver opcional
    def __init__(self, driver=None, default_timeout: int = 30):
        self.driver = driver
        self.default_timeout = default_timeout
        self._wait = WebDriverWait(self.driver, self.default_timeout) if self.driver else None

    # Inicializa y devuelve el driver de Selenium.
    def get_driver(self):
        chrome_options = Options()
        chrome_options.add_argument('--start-maximized')
        driver = webdriver.Chrome(options=chrome_options)
        # asociar driver a la instancia para que otros métodos puedan usarlo
        self.driver = driver
        self._wait = WebDriverWait(self.driver, self.default_timeout)
        return driver

    # Cierra el driver de Selenium.
    def quit_driver(self, driver):
        driver.quit()

    # Abre la URL principal del sitio en el navegador.
    def open_page(self, driver=None):    
        if driver is None:
            driver = self.driver
        driver.get(self.URL)

    # Ingresa texto en un campo de entrada (input).
    def enter_text(self, element, text):
        element.clear()
        element.send_keys(text)

    # Hace clic sobre un elemento WebElement.
    def clickElement(self, element):
        elem = self.wait_for(element, "clickable")
        elem.click()

    # Metodo wait para esperar condiciones en elementos
    def wait_for(self, element, attribute):
        """Espera hasta que un elemento tenga un atributo específico."""
        if not self.driver:
            raise RuntimeError("No WebDriver asociado a esta instancia de Base. Inicializa el driver antes de usar wait_for.")
        wait = WebDriverWait(self.driver, self.default_timeout)

        attribute_map = {
            "clickable": EC.element_to_be_clickable(element),
            "visible": EC.visibility_of(element),
            "invisible": EC.invisibility_of_element(element),
            "staleness": EC.staleness_of(element),
        }

        if attribute not in attribute_map:
            raise ValueError(
                f"Condición '{attribute}' no soportada. "
                f"Usa: {list(attribute_map.keys())}"
            )

        return wait.until(attribute_map[attribute])