from __future__ import annotations

from typing import Dict, Type, TypeVar

from helpers import config
from pages.base import Base
from pages.home_page import HomePage
from pages.login_page import LoginPage

T = TypeVar("T", bound=Base)


class ObjectManager:
    """Instancia y comparte PageObjects reutilizables."""

    def __init__(
        self,
        timeout: int = config.DEFAULT_WAIT_TIMEOUT,
        *,
        use_profile: bool = True,
        reset_profile: bool = False,
    ):
        self._base = Base(default_timeout=timeout)
        self.driver = None
        self._page_cache: Dict[type[Base], Base] = {}
        self.use_profile = use_profile
        self.start_driver(reset_profile=reset_profile, use_profile=use_profile)

    def start_driver(self, *, reset_profile: bool = False, use_profile: bool | None = None):
        if self.driver:
            self.quit()
        desired_profile = use_profile if use_profile is not None else self.use_profile
        if reset_profile:
            self._base.reset_profile()
        # Evita sesiones inconsistentes cuando queda un Chrome zombie usando cualquier perfil.
        self._base.close_residual_chrome()
        self.driver = self._base.get_driver(use_profile=desired_profile)
        self.use_profile = desired_profile
        self._base.open_page(url=config.HOME_URL)
        self._page_cache.clear()
        return self.driver

    def restart(self, *, reset_profile: bool = False, use_profile: bool | None = None):
        return self.start_driver(reset_profile=reset_profile, use_profile=use_profile)

    def get(self, page_cls: Type[T]) -> T:
        if page_cls not in self._page_cache:
            self._page_cache[page_cls] = page_cls(self.driver)
        return self._page_cache[page_cls]

    @property
    def base(self) -> Base:
        return self._base

    @property
    def home(self) -> HomePage:
        return self.get(HomePage)

    @property
    def login(self) -> LoginPage:
        return self.get(LoginPage)

    def quit(self):
        if self.driver:
            self._base.quit_driver(self.driver)
            self.driver = None
