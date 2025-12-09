import os
from pathlib import Path

BASE_URL = os.getenv("REPORTFIA_BASE_URL", "https://reportfia.deras.dev").rstrip("/")
LOGIN_URL = f"{BASE_URL}/iniciar-sesion"
HOME_URL = f"{BASE_URL}/inicio"

DEFAULT_USER = os.getenv("REPORTFIA_USER", "zz11001")
DEFAULT_PASSWORD = os.getenv("REPORTFIA_PASSWORD", "Admin123$")
# DEFAULT_PASSWORD = os.getenv("REPORTFIA_PASSWORD", "Hl3oFfmQEethf7bx")
YOPMAIL_URL = os.getenv("REPORTFIA_YOPMAIL_URL", "https://yopmail.com/es/")

ASSIGNEE_USER = os.getenv("REPORTFIA_ASSIGNEE_USER", "ee31001")
ASSIGNEE_PASSWORD = os.getenv("REPORTFIA_ASSIGNEE_PASSWORD", "adminadmin")

FUNDS_USER = os.getenv("REPORTFIA_FUNDS_USER", "rr11001")
FUNDS_PASSWORD = os.getenv("REPORTFIA_FUNDS_PASSWORD", "pass123")

MAINTENANCE_USER = os.getenv("REPORTFIA_MAINTENANCE_USER", "aa11001")
MAINTENANCE_PASSWORD = os.getenv("REPORTFIA_MAINTENANCE_PASSWORD", "pass123")

PROFILE_USER = os.getenv("REPORTFIA_PROFILE_USER", "hg16037")
PROFILE_PASSWORD = os.getenv("REPORTFIA_PROFILE_PASSWORD", "pass1234*")
PROFILE_PASSWORD_OTHER = os.getenv("REPORTFIA_PROFILE_PASSWORD_OTHER", "pass1234")

FUN27_EMPLOYEE_NAME = os.getenv("REPORTFIA_FUN27_EMPLOYEE", "")

# Prueba1
FUN27_ENTITY_NAME = os.getenv("REPORTFIA_FUN27_ENTITY", "LOGÍSTICA Y GESTIÓN")
FUN27_POSITION_NAME = os.getenv("REPORTFIA_FUN27_POSITION", "MOTORISTA")

# Prueba2
# FUN27_ENTITY_NAME = os.getenv("REPORTFIA_FUN27_ENTITY", "LOGÍSTICA Y GESTIÓN")
# FUN27_POSITION_NAME = os.getenv("REPORTFIA_FUN27_POSITION", "GESTOR DE LOGÍSTICA DE EVENTOS PROTOCOLARES")

# Prueba3
# FUN27_ENTITY_NAME = os.getenv("REPORTFIA_FUN27_ENTITY", "UNIDAD DE PLANIFICACIÓN")
# FUN27_POSITION_NAME = os.getenv("REPORTFIA_FUN27_POSITION", "PLANIFICADOR DE RIESGOS")

FUN27_STATUS_LABEL = os.getenv("REPORTFIA_FUN27_STATUS", "Activo")
FUN27_SUCCESS_MESSAGE = os.getenv("REPORTFIA_FUN27_SUCCESS", "Puesto asignado exitosamente")
_FUN27_EMPLOYEE_POOL = os.getenv("REPORTFIA_FUN27_EMPLOYEES", "")
if _FUN27_EMPLOYEE_POOL.strip():
    FUN27_EMPLOYEE_CANDIDATES = tuple(
        name.strip() for name in _FUN27_EMPLOYEE_POOL.split("|") if name.strip()
    )
elif FUN27_EMPLOYEE_NAME.strip():
    FUN27_EMPLOYEE_CANDIDATES = (FUN27_EMPLOYEE_NAME.strip(),)
else:
    FUN27_EMPLOYEE_CANDIDATES = ()
_FUN27_ALLOWED_ENTITIES = os.getenv(
    "REPORTFIA_FUN27_ALLOWED_ENTITIES",
    "DECANATO|UNIDAD DE PLANIFICACION|DESARROLLO E INFRAESTRUCTURA|LOGISTICA Y GESTION|MANTENIMIENTO Y SERVICIOS GENERALES",
)
FUN27_ALLOWED_ENTITIES = tuple(
    name.strip() for name in _FUN27_ALLOWED_ENTITIES.split("|") if name.strip()
)

CHROME_PROFILE_DIR = Path(os.getenv("REPORTFIA_PROFILE_DIR", "./.chrome-profile-reportfia")).resolve()
CHROME_SUBPROFILE = os.getenv("REPORTFIA_CHROME_PROFILE", "ReportFIAProfile")

DEFAULT_WAIT_TIMEOUT = int(os.getenv("REPORTFIA_WAIT_TIMEOUT", "150"))

SUPPORTED_BROWSERS = ("chrome", "edge")
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DRIVERS_DIR = Path(os.getenv("REPORTFIA_DRIVERS_DIR", str(PROJECT_ROOT / "drivers"))).resolve()
_DRIVER_HINTS = {
    "chrome": ("REPORTFIA_CHROME_DRIVER", "chromedriver.exe"),
    "edge": ("REPORTFIA_EDGE_DRIVER", "msedgedriver.exe"),
}


def get_browser_choice(default: str = "chrome") -> str:
    """Return a sanitized browser choice honoring REPORTFIA_BROWSER."""
    candidate = os.getenv("REPORTFIA_BROWSER", default).strip().lower()
    return candidate if candidate in SUPPORTED_BROWSERS else default


def get_driver_override(browser: str):
    """Return a filesystem Path for a bundled driver binary when available."""
    hint = _DRIVER_HINTS.get(browser)
    if not hint:
        return None
    env_var, default_name = hint
    env_value = os.getenv(env_var)
    candidates = []
    if env_value:
        candidates.append(Path(env_value).expanduser())
    candidates.append(DRIVERS_DIR / default_name)
    for candidate in candidates:
        try:
            resolved = candidate.expanduser().resolve()
        except FileNotFoundError:
            resolved = candidate.expanduser()
        if resolved.is_file():
            return resolved
    return None
