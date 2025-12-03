from selenium.webdriver.common.by import By

from pages.base import Base


class MaintenanceFundsPage(Base):
    _table = (By.CSS_SELECTOR, "table")

    def table_is_visible(self) -> bool:
        elemento = self.wait_for_locator(self._table, "visible")
        return elemento is not None
