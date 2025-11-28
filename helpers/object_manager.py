from pages.base import Base
from pages.home_page import HomePage
from pages.login_page import LoginPage

class ObjectManager:
    """
    Gestor de objetos que inicializa el driver y provee PageObjects reutilizables.
    Uso: manager = ObjectManager(); manager.home / manager.login / manager.base
    """
    def __init__(self, timeout: int = 30):
        self._base = Base(default_timeout=timeout)
        # Inicia el driver y asocia al Base
        self.driver = self._base.get_driver()
        self._base.open_page(self.driver)

        # Placeholders para PageObjects (creación lazy)
        self._home = None
        self._login = None

    @property
    def base(self) -> Base:
        return self._base

    @property
    def home(self) -> HomePage:
        if self._home is None:
            self._home = HomePage(self.driver)
        return self._home

    @property
    def login(self) -> LoginPage:
        if self._login is None:
            self._login = LoginPage(self.driver)
        return self._login

    def quit(self):
        self._base.quit_driver(self.driver)