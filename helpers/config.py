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

CHROME_PROFILE_DIR = Path(os.getenv("REPORTFIA_PROFILE_DIR", "./.chrome-profile-reportfia")).resolve()
CHROME_SUBPROFILE = os.getenv("REPORTFIA_CHROME_PROFILE", "ReportFIAProfile")

DEFAULT_WAIT_TIMEOUT = int(os.getenv("REPORTFIA_WAIT_TIMEOUT", "150"))
