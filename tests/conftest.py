import pytest

from helpers.object_manager import ObjectManager


@pytest.fixture()
def manager(request):
    clean_profile = request.node.get_closest_marker("clean_profile") is not None
    no_profile = request.node.get_closest_marker("no_profile") is not None
    use_profile = not no_profile
    om = ObjectManager(use_profile=use_profile, reset_profile=clean_profile)
    yield om
    om.quit()


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

    order = [
        "test_fun_01.py",
        "test_fun_06.py",
        "test_fun_36.py",
        "test_fun_38.py",
        "test_fun_49.py",
        "test_fun_65.py",
        "test_fun_75.py",
        "test_fun_72.py",
        "test_seg_16.py",
        "test_seg_17.py",
    ]

    def sort_key(item):
        node = item.nodeid
        for idx, name in enumerate(order):
            if name in node:
                return (idx, node)
        return (len(order), node)

    items.sort(key=sort_key)
