import time

from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select

from pages.base import Base


class ReportAssignmentForm(Base):
    _entity_select = (By.ID, "entidad")
    _employees_loading = (By.ID, "empleados-loading")
    _employee_search = (By.CSS_SELECTOR, ".search-available")
    _employee_items = (By.CSS_SELECTOR, ".available-items li")
    _employee_add_button = (By.CSS_SELECTOR, "button.add-item")
    _employee_hidden = (By.CSS_SELECTOR, "input[name='id_empleados_puestos']")
    _supervisor_container = (By.ID, "supervisor-pick")
    _supervisor_search_inputs = (By.CSS_SELECTOR, "#supervisor-pick input[placeholder='Buscar...']")
    _supervisor_available_items = (By.CSS_SELECTOR, "#supervisor-pick .max-h-56 li")
    _resource_add_buttons = (By.CSS_SELECTOR, ".btn-add-item")
    _category_select = (By.ID, "id_categoria_reporte")
    _comment_field = (By.ID, "comentario")
    _submit_button = (By.ID, "enviarAsignacion")
    _notification = (By.CSS_SELECTOR, "div.notyf__message")

    def reset_form(self):
        script = """
        const assignedList = document.querySelector('.assigned-items');
        if (assignedList) assignedList.innerHTML = '';
        const hiddenEmployees = document.querySelector("input[name='id_empleados_puestos']");
        if (hiddenEmployees) hiddenEmployees.value = '';
        const supervisorPick = document.getElementById('supervisor-pick');
        if (supervisorPick) {
            supervisorPick.querySelectorAll("input[name='id_supervisores[]']").forEach(el => el.remove());
            const selectedList = supervisorPick.querySelector("ul.max-h-56:nth-of-type(2)");
            if (selectedList) selectedList.innerHTML = '';
        }
        const selectedGoods = document.getElementById('selected-bienes-table-body');
        if (selectedGoods) selectedGoods.innerHTML = '';
        const goodsInput = document.getElementById('id_bienes');
        if (goodsInput) goodsInput.value = '[]';
        """
        self.driver.execute_script(script)

    def select_entity(self, entity_name: str):
        select = Select(self.wait_for_locator(self._entity_select, "visible", timeout=10))
        select.select_by_visible_text(entity_name)
        self._wait_for_employees_loaded()

    def _wait_for_employees_loaded(self):
        try:
            loader = self.wait_for_locator(self._employees_loading, "presence", timeout=2)
            self.wait_for_locator(self._employees_loading, "invisible", timeout=10)
        except TimeoutException:
            time.sleep(0.5)

    def add_employee(self, employee_name: str):
        self._search(self._employee_search, employee_name)
        item = self._find_list_item(self._employee_items, employee_name)
        item.click()
        add_btn = self.wait_for_locator(self._employee_add_button, "clickable", timeout=5)
        self.safe_click(add_btn)
        employee_id = item.get_attribute("data-item-id") or ""
        self._ensure_employee_registered(employee_id)

    def _ensure_employee_registered(self, employee_id: str):
        hidden = self.wait_for_locator(self._employee_hidden, "presence", timeout=5)
        deadline = time.time() + 5
        while time.time() < deadline:
            value = (hidden.get_attribute("value") or "").strip()
            if not employee_id or employee_id in value:
                return
            time.sleep(0.2)
        raise TimeoutException("No fue posible registrar el subalterno seleccionado.")

    def add_supervisor(self, supervisor_name: str):
        self._search(self._supervisor_search_inputs, supervisor_name)
        item = self._find_list_item(self._supervisor_available_items, supervisor_name)
        button = item.find_element(By.TAG_NAME, "button")
        self.safe_click(button)

    def add_first_resource(self):
        button = self.wait_for_locator(self._resource_add_buttons, "clickable", timeout=5)
        self.scroll_into_view(button)
        self.safe_click(button)

    def select_category(self, category_text: str):
        select = Select(self.wait_for_locator(self._category_select, "visible", timeout=5))
        select.select_by_visible_text(category_text)

    def set_comment(self, text: str):
        self.type_into(self._comment_field, text, clear=True)

    def submit(self) -> str:
        button = self.wait_for_locator(self._submit_button, "clickable", timeout=5)
        self.safe_click(button)
        try:
            return self.wait_for_locator(self._notification, "visible", timeout=10).text.strip()
        except TimeoutException:
            return ""

    def _search(self, locator, term: str):
        if isinstance(locator, tuple):
            target = self.wait_for_locator(locator, "visible", timeout=5)
            target.clear()
            target.send_keys(term)
        else:
            inputs = self.driver.find_elements(*locator)
            if not inputs:
                return
            target = inputs[0]
            target.clear()
            target.send_keys(term)
        time.sleep(0.3)

    def _find_list_item(self, locator, text: str):
        deadline = time.time() + 5
        while time.time() < deadline:
            items = self.driver.find_elements(*locator)
            for item in items:
                if not item.is_displayed():
                    continue
                if text.lower() in item.text.lower():
                    self.scroll_into_view(item)
                    return item
            time.sleep(0.2)
        raise TimeoutException(f"No se encontró el elemento con texto '{text}'.")
