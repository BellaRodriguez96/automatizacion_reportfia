from __future__ import annotations

import time
from typing import Iterable, Sequence

from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select

from pages.base import Base
from helpers import config


EMPLOYEE_PICK_BASE_START = 30
EMPLOYEE_PICK_BASE_END = 40
EMPLOYEE_KEYWORD_TARGETS = ("prueba", "pom", "qa")


class AssignPositionModal(Base):
    _modal_candidates = (
        (By.ID, "assign-position-modal"),
        (By.CSS_SELECTOR, "[data-modal-placement][role='dialog']"),
        (By.ID, "asignacion-form"),
        (By.CSS_SELECTOR, "form[action*='empleados-puestos']"),
    )
    _employee_search_input = (By.ID, "search-empleado")
    _employee_dropdown = (By.ID, "dropdown-empleado")
    _employee_option_locator = (By.CSS_SELECTOR, "#dropdown-empleado li[data-value]")
    _employee_hidden_input = (By.ID, "empleado")
    _entity_select_candidates = (
        (By.ID, "entidad"),
        (By.NAME, "entidad"),
        (By.CSS_SELECTOR, "select[name='entidad']"),
    )
    _position_select_candidates = (
        (By.ID, "puesto"),
        (By.NAME, "puesto"),
        (By.CSS_SELECTOR, "select[name='puesto']"),
    )
    _status_select_candidates = (
        (By.ID, "estado"),
        (By.NAME, "estado"),
        (By.CSS_SELECTOR, "select[name='estado']"),
    )
    _submit_button_candidates = (
        (By.CSS_SELECTOR, "button[type='submit'][form='asignacion-form']"),
        (By.CSS_SELECTOR, "form#asignacion-form button[type='submit']"),
        (
            By.XPATH,
            "//button[contains(translate(normalize-space(.), 'ÁÉÍÓÚáéíóú', 'AEIOUaeiou'), 'GUARDAR')]",
        ),
    )
    _notification = (By.CSS_SELECTOR, "div.notyf__message")

    def wait_until_ready(self):
        self.wait_for_any_locator(self._modal_candidates, "visible", timeout=15)

    def fill_assignment_form(
        self,
        *,
        employee_name: str | Sequence[str] | None,
        entity_name: str | None,
        position_name: str | None,
        status_label: str | None,
        exclude_entities: set[str] | None = None,
        employee_index_offset: int = 0,
    ) -> dict[str, str]:
        snapshot: dict[str, str] = {}
        snapshot["employee"] = self._select_employee(employee_name, offset=employee_index_offset)
        entity_label, position_label = self._choose_entity_and_position(
            entity_name, position_name, exclude_entities=exclude_entities or set()
        )
        snapshot["entity"] = entity_label
        snapshot["position"] = position_label
        snapshot["status"] = self._select_status(status_label)
        return snapshot

    def submit(self) -> str:
        button = self.wait_for_any_locator(self._submit_button_candidates, "clickable", timeout=10)
        self.scroll_into_view(button)
        self.safe_click(button)
        message = self._wait_for_notification()
        self._wait_until_closed()
        return message

    def _wait_for_notification(self) -> str:
        try:
            toast = self.wait_for_locator(self._notification, "visible", timeout=15)
            return toast.text.strip()
        except TimeoutException:
            return ""

    def _wait_until_closed(self):
        def _modal_closed(_):
            for locator in self._modal_candidates:
                try:
                    element = self.driver.find_element(*locator)
                except Exception:
                    continue
                if element.is_displayed():
                    return False
            return True

        try:
            self.wait_for_condition(_modal_closed, timeout=10)
        except TimeoutException:
            pass

    def _select_employee(self, preferred: str | Sequence[str] | None, *, offset: int = 0) -> str:
        search_input, dropdown = self._prepare_employee_dropdown("", clear_input=True)
        remaining = max(offset, 0)
        for keyword in EMPLOYEE_KEYWORD_TARGETS:
            options = self._options_for_keyword(keyword, search_input=search_input, dropdown=dropdown, timeout=2)
            if not options:
                continue
            if remaining < len(options):
                index = max(0, len(options) - 1 - remaining)
                return self._choose_employee_option(options[index])
            remaining -= len(options)
        raise TimeoutException("No se pudo seleccionar un empleado con las palabras clave requeridas.")

    def _options_for_keyword(self, keyword: str, *, search_input=None, dropdown=None, timeout: float = 2.0):
        term = (keyword or "").strip()
        if not term:
            return []
        search_input, dropdown = self._prepare_employee_dropdown(
            term, search_input=search_input, dropdown=dropdown, clear_input=True
        )
        end = time.time() + timeout
        while time.time() < end:
            options = self.driver.find_elements(*self._employee_option_locator)
            visible_options = []
            for option in options:
                if not option.text.strip():
                    continue
                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", option)
                if self._option_is_visible(option, dropdown):
                    visible_options.append(option)
            if visible_options:
                return visible_options
            time.sleep(0.05)
        return []

    def _first_visible_employee_option(self):
        _, dropdown = self._prepare_employee_dropdown("", clear_input=True)
        end = time.time() + 5
        while time.time() < end:
            options = self.driver.find_elements(*self._employee_option_locator)
            for option in options:
                if self._option_is_visible(option, dropdown):
                    return option
            time.sleep(0.1)
        return None

    def _prepare_employee_dropdown(self, term: str, *, search_input=None, dropdown=None, clear_input: bool = False):
        search_input = search_input or self.wait_for_locator(self._employee_search_input, "visible", timeout=5)
        dropdown = dropdown or self.wait_for_locator(self._employee_dropdown, "presence", timeout=5)
        self.safe_click(search_input)
        if clear_input:
            search_input.clear()
        if term:
            search_input.clear()
            search_input.send_keys(term)
        self.driver.execute_script("arguments[0].classList.remove('hidden');", dropdown)
        return search_input, dropdown

    def _option_is_visible(self, option, dropdown) -> bool:
        try:
            if dropdown.get_attribute("class") and "hidden" in dropdown.get_attribute("class"):
                return False
            return option.is_displayed()
        except Exception:
            return False

    def _choose_employee_option(self, option):
        label = option.text.strip()
        self.scroll_into_view(option)
        option.click()
        self._wait_for_hidden_employee_value()
        return label

    def _wait_for_hidden_employee_value(self, timeout: int = 5):
        hidden = self.wait_for_locator(self._employee_hidden_input, "presence", timeout=timeout)
        end = time.time() + timeout
        while time.time() < end:
            value = (hidden.get_attribute("value") or "").strip()
            if value:
                return value
            time.sleep(0.2)
        raise TimeoutException("No se registro el empleado seleccionado en el formulario.")

    def _choose_entity_and_position(self, entity_name: str | None, position_name: str | None, *, exclude_entities: set[str]):
        if entity_name and position_name:
            entity_label = self._select_entity(entity_name)
            self._wait_for_select_options(self._position_select_candidates, timeout=4, strict=True)
            position_label = self._select_option(self._position_select_candidates, position_name, fallback_to_first=False)
            return entity_label, position_label

        preferences: list[str] = []
        if entity_name:
            preferences.append(entity_name)

        for label in config.FUN27_ALLOWED_ENTITIES:
            if not label:
                continue
            if entity_name and self._normalize(label) == self._normalize(entity_name):
                continue
            preferences.append(label)

        tried: set[str] = set(exclude_entities)
        attempts = 0
        last_error: Exception | None = None

        for label in preferences:
            label = (label or "").strip()
            if not label or self._normalize(label) in {self._normalize(x) for x in tried}:
                continue
            tried.add(label)
            attempts += 1

            current_label = self._select_entity(label)
            has_positions = self._wait_for_select_options(self._position_select_candidates, timeout=6, strict=False)
            if not has_positions:
                if attempts >= 3:
                    raise TimeoutException("No se cargaron puestos disponibles tras intentar 3 entidades distintas.")
                continue

            try:
                position_label = self._select_option(self._position_select_candidates, position_name, fallback_to_first=True)
                return current_label, position_label
            except TimeoutException as exc:
                last_error = exc
                if attempts >= 5:
                    break
                continue

        raise last_error or TimeoutException("No fue posible seleccionar un puesto valido para las entidades evaluadas.")

    def _select_entity(self, entity_label: str) -> str:
        select_element = self._find_select(self._entity_select_candidates)
        selected_text = self._select_option_from_element(select_element, entity_label)
        self._trigger_change(select_element)
        return selected_text

    def _select_status(self, status_label: str | None) -> str:
        return self._select_option(self._status_select_candidates, status_label)

    def _select_option(self, locator_candidates, target_text: str | None, *, fallback_to_first: bool = False) -> str:
        select_element = self._find_select(locator_candidates)
        return self._select_option_from_element(select_element, target_text, fallback_to_first=fallback_to_first)

    def _select_option_from_element(self, select_element, target_text: str | None, *, fallback_to_first: bool = False) -> str:
        selector = Select(select_element)
        if target_text:
            try:
                self._select_by_text(selector, target_text)
            except TimeoutException:
                if fallback_to_first:
                    self._select_first_valid(selector)
                else:
                    raise
        else:
            self._select_first_valid(selector)
        return selector.first_selected_option.text.strip()

    def _find_select(self, locator_candidates):
        last_error: Exception | None = None
        for locator in locator_candidates:
            try:
                element = self.wait_for_locator(locator, "visible", timeout=5)
            except TimeoutException as exc:
                last_error = exc
                continue
            if element.tag_name.lower() == "select":
                return element
        raise last_error or TimeoutException("No se encontro el campo solicitado en el modal de asignacion.")

    def _select_by_text(self, selector: Select, desired_text: str):
        normalized_target = self._normalize(desired_text)
        for option in selector.options:
            option_text = option.text.strip()
            if not option_text:
                continue
            if normalized_target == self._normalize(option_text) or normalized_target in self._normalize(option_text):
                option.click()
                return
        raise TimeoutException(f"No fue posible seleccionar la opcion '{desired_text}'.")

    def _select_first_valid(self, selector: Select):
        for option in selector.options:
            label = option.text.strip()
            if not label:
                continue
            normalized = self._normalize(label)
            if "seleccione" in normalized or "selecciona" in normalized:
                continue
            option.click()
            return
        raise TimeoutException("No se encontro una opcion valida para seleccionar.")

    def _wait_for_select_options(self, locator_candidates, timeout: int = 10, *, strict: bool = True):
        end = time.time() + timeout
        while time.time() < end:
            select_element = self._find_select(locator_candidates)
            options = select_element.find_elements(By.TAG_NAME, "option")
            valid_options = [
                opt for opt in options if (opt.get_attribute("value") or "").strip()
            ]
            if valid_options:
                return True
            time.sleep(0.15)
        if strict:
            raise TimeoutException("Las opciones requeridas no se cargaron en el selector solicitado.")
        return False

    def _trigger_change(self, element):
        try:
            self.driver.execute_script("if (arguments[0]) { arguments[0].dispatchEvent(new Event('change', {bubbles: true})); }", element)
        except Exception:
            pass

    def _employee_option_by_index_range(self, start: int, end: int):
        _, dropdown = self._prepare_employee_dropdown("", clear_input=True)
        options = self.driver.find_elements(*self._employee_option_locator)
        for idx, option in enumerate(options, start=1):
            if idx < start or idx > end:
                continue
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", option)
            if self._option_is_visible(option, dropdown):
                return option
        return None


    @staticmethod
    def _normalize(value: str) -> str:
        replacements = str.maketrans("ÁÉÍÓÚÜÑáéíóúüñ", "AEIOUUNaeiouun")
        return value.strip().lower().translate(replacements)
