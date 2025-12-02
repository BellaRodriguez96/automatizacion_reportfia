import os
from pathlib import Path

BASE_URL = os.getenv("REPORTFIA_BASE_URL", "https://reportfia.deras.dev").rstrip("/")
LOGIN_URL = f"{BASE_URL}/iniciar-sesion"
HOME_URL = f"{BASE_URL}/inicio"

DEFAULT_USER = os.getenv("REPORTFIA_USER", "zz11001")
DEFAULT_PASSWORD = os.getenv("REPORTFIA_PASSWORD", "Admin123$")
# DEFAULT_PASSWORD = os.getenv("REPORTFIA_PASSWORD", "Hl3oFfmQEethf7bx")
YOPMAIL_URL = os.getenv("REPORTFIA_YOPMAIL_URL", "https://yopmail.com/es/")

CHROME_PROFILE_DIR = Path(os.getenv("REPORTFIA_PROFILE_DIR", "./.chrome-profile-reportfia")).resolve()
CHROME_SUBPROFILE = os.getenv("REPORTFIA_CHROME_PROFILE", "ReportFIAProfile")

DEFAULT_WAIT_TIMEOUT = int(os.getenv("REPORTFIA_WAIT_TIMEOUT", "150"))
