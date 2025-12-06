import time

import pytest

from helpers.object_manager import ObjectManager
from pages.base import Base
from pages.login_page import LoginPage

AA_BLOCK_TESTS = [
    "test_fun_01.py",
    "test_fun_06.py",
    "test_fun_19.py",
    "test_fun_40.py",
    "test_fun_41.py",
    "test_fun_53.py",
    "test_fun_36.py",
    "test_fun_38.py",
    "test_fun_49.py",
    "test_fun_56.py",
    "test_fun_57.py",
    "test_fun_59.py",
    "test_fun_65.py",
    "test_fun_69.py",
    "test_fun_75.py",
    "test_fun_15.py",
    "test_fun_39.py",
    "test_fun_46.py",
    "test_fun_51.py",
    "test_fun_52.py",
    "test_fun_54.py",
]
EE_BLOCK_TESTS = ["test_fun_43.py"]
RR_BLOCK_TESTS = ["test_fun_45.py", "test_fun_48.py"]
MIXED_BLOCK_TESTS = [
    "test_fun_72.py",
    "test_fun_74.py",
    "test_fun_79.py",
    "test_fun_70.py",
    "test_fun_76.py",
    "test_seg_04.py",
    "test_seg_16.py",
    "test_seg_17.py",
]

BLOCK_DEFINITIONS = [
    {
        "name": "profile_block",
        "tests": ["test_fun_08.py"],
        "reset_before_first": True,
        "clear_before_each": True,
    },
    {
        "name": "aa_persist_block",
        "tests": AA_BLOCK_TESTS,
        "reset_before_first": False,
        "clear_before_each": False,
    },
    {
        "name": "ee_forced_fresh",
        "tests": EE_BLOCK_TESTS,
        "reset_before_first": True,
        "clear_before_each": True,
    },
    {
        "name": "rr_forced_fresh",
        "tests": RR_BLOCK_TESTS,
        "reset_before_first": True,
        "clear_before_each": True,
    },
    {
        "name": "mixed_block",
        "tests": MIXED_BLOCK_TESTS,
        "reset_before_first": True,
        "clear_before_each": True,
    },
]


class BlockController:
    def __init__(self, blocks):
        self.blocks = blocks
        self._state = {block["name"]: {"started": False, "finished": False} for block in blocks}

    def get_block(self, nodeid: str):
        for block in self.blocks:
            for pattern in block["tests"]:
                if pattern in nodeid:
                    return block
        return None

    def is_first(self, block, nodeid: str) -> bool:
        return block["tests"] and block["tests"][0] in nodeid

    def is_last(self, block, nodeid: str) -> bool:
        return block["tests"] and block["tests"][-1] in nodeid

    def mark_started(self, block):
        self._state[block["name"]]["started"] = True

    def mark_finished(self, block):
        self._state[block["name"]]["finished"] = True


def pytest_configure(config):
    config._block_controller = BlockController(BLOCK_DEFINITIONS)


@pytest.fixture(scope="session")
def session_manager():
    om = ObjectManager()
    yield om
    om.quit()


@pytest.fixture()
def manager(request, session_manager):
    clean_profile = request.node.get_closest_marker("clean_profile") is not None
    no_profile = request.node.get_closest_marker("no_profile") is not None
    use_profile = not no_profile

    def _driver_alive() -> bool:
        driver = session_manager.driver
        if not driver:
            return False
        try:
            driver.current_url
            return True
        except Exception:
            return False

    driver_alive = _driver_alive()

    if clean_profile:
        session_manager._ensure_driver_active()
        login_page = session_manager.get(LoginPage)
        login_page.logout_and_clear()
    elif not driver_alive:
        session_manager.restart(reset_profile=True, use_profile=use_profile)
    elif session_manager.driver is None:
        session_manager.start_driver(use_profile=use_profile)
    elif session_manager.use_profile != use_profile:
        session_manager.restart(reset_profile=False, use_profile=use_profile)

    session_manager._ensure_driver_active()
    return session_manager


@pytest.fixture(autouse=True)
def block_persistence_guard(request, session_manager):
    controller = getattr(request.config, "_block_controller", None)
    if not controller:
        yield
        return

    block = controller.get_block(request.node.nodeid)
    if not block:
        yield
        return

    login_page = session_manager.get(LoginPage)
    is_first = controller.is_first(block, request.node.nodeid)
    if is_first:
        controller.mark_started(block)
        if block.get("reset_before_first") or block.get("clear_before_each"):
            login_page.logout_and_clear()
    elif block.get("clear_before_each"):
        login_page.logout_and_clear()

    yield

    if controller.is_last(block, request.node.nodeid):
        login_page.logout_and_clear()
        controller.mark_finished(block)


@pytest.fixture(autouse=True)
def pause_after_test():
    yield
    time.sleep(2)


def pytest_collection_modifyitems(config, items):
    filtered = []
    deselected = []
    for item in items:
        if "tests/test_bella.py" in item.nodeid:
            deselected.append(item)
        else:
            filtered.append(item)
    if deselected:
        config.hook.pytest_deselected(items=deselected)
    items[:] = filtered

    order = []
    for block in BLOCK_DEFINITIONS:
        order.extend(block["tests"])
    order.extend(
        [
            "test_fun_71.py",
            "test_fun_73.py",
            "test_seg_14.py",
            "test_seg_19.py",
        ]
    )

    def sort_key(item):
        node = item.nodeid
        for idx, name in enumerate(order):
            if name in node:
                return (idx, node)
        return (len(order), node)

    items.sort(key=sort_key)


def pytest_sessionfinish(session, exitstatus):
    """Clean Chrome persistence at the end of the suite."""
    Base().reset_profile()
