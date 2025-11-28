import pathlib
import subprocess
import sys

ROOT_DIR = pathlib.Path(__file__).parent.resolve()
TESTS_DIR = ROOT_DIR / "tests"

TEST_PATTERN = "test_*_[0-9][0-9].py"
FUN01_PATH = TESTS_DIR / "test_fun_01.py"

def discover_tests():
    return sorted(TESTS_DIR.glob(TEST_PATTERN))

def run_fun01_reset() -> bool:
    """Ejecuta test_fun_01.py para restablecer la sesion (incluido el 2FA)."""
    if not FUN01_PATH.exists():
        return False

    print("\nIntentando restablecer la sesion ejecutando test_fun_01.py ...")
    cmd = [sys.executable, str(FUN01_PATH), "--no-reset-profile"]
    result = subprocess.run(cmd, cwd=ROOT_DIR)
    if result.returncode == 0:
        print("Sesion restablecida correctamente. Reintentando prueba fallida...\n")
        return True

    print("No se pudo restablecer la sesion automaticamente (test_fun_01.py fallo).")
    return False

def run_test(path: pathlib.Path, allow_retry: bool = True, cmd: list[str] | None = None) -> int:
    """Ejecuta una prueba y, si falla, intenta una vez restaurar el login."""
    command = cmd or [sys.executable, str(path)]
    result = subprocess.run(command, cwd=ROOT_DIR)
    if result.returncode == 0:
        return 0

    if allow_retry and run_fun01_reset():
        return run_test(path, allow_retry=False, cmd=command)

    return result.returncode

def main() -> int:
    tests = discover_tests()
    if not tests:
        print("No se encontraron pruebas que coincidan con el patron.")
        return 1

    failures = []
    for test_path in tests:
        print("=" * 80)
        print(f"Ejecutando {test_path.relative_to(ROOT_DIR)}")
        print("=" * 80)
        allow_retry = test_path.name != "test_fun_01.py"
        cmd = [sys.executable, str(test_path)]
        if test_path.name == "test_fun_01.py":
            cmd.append("--no-reset-profile")
        exit_code = run_test(test_path, allow_retry=allow_retry, cmd=cmd)
        if exit_code != 0:
            failures.append(test_path.name)

    if failures:
        print("\nPruebas con errores:")
        for name in failures:
            print(f" - {name}")
        return 1

    print("\nTodas las pruebas finalizaron correctamente.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
