import pathlib
import subprocess
import sys

ROOT_DIR = pathlib.Path(__file__).parent.resolve()


def main() -> int:
    """Ejecuta la suite completa usando pytest."""
    cmd = [sys.executable, "-m", "pytest", "tests"]
    return subprocess.run(cmd, cwd=ROOT_DIR).returncode


if __name__ == "__main__":
    raise SystemExit(main())
