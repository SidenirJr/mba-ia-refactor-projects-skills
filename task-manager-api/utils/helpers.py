"""Helpers e constantes compartilhados (antes definidos e ignorados; agora realmente usados)."""
import re
from datetime import datetime, timezone

EMAIL_RE = re.compile(r"^[a-zA-Z0-9+_.-]+@[a-zA-Z0-9.-]+$")

VALID_STATUSES = ["pending", "in_progress", "done", "cancelled"]
VALID_ROLES = ["user", "admin", "manager"]
MAX_TITLE_LENGTH = 200
MIN_TITLE_LENGTH = 3
MIN_PASSWORD_LENGTH = 4
DEFAULT_PRIORITY = 3
MIN_PRIORITY = 1
MAX_PRIORITY = 5
DEFAULT_COLOR = "#000000"


def utcnow():
    """UTC naive — substitui o `datetime.utcnow()` deprecado mantendo compatibilidade
    com os datetimes naive lidos do SQLite (evita mistura de aware/naive)."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def is_valid_email(email):
    return bool(email and EMAIL_RE.match(email))


def parse_date(date_string):
    for fmt in ("%Y-%m-%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(date_string, fmt)
        except (ValueError, TypeError):
            continue
    return None


def calculate_percentage(part, total):
    if not total:
        return 0
    return round((part / total) * 100, 2)
