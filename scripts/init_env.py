"""Create a private local environment file without printing secrets."""

import secrets
from pathlib import Path

path = Path(__file__).resolve().parents[1] / ".env"
if path.exists():
    raise SystemExit(".env already exists; left unchanged")
path.write_text(
    "DATABASE_URL=postgresql+psycopg://ledger:ledger_local@localhost:5438/ledger\nDEMO_PASSWORD="
    + secrets.token_urlsafe(24)
    + "\n"
)
path.chmod(0o600)
print(
    "Created private .env. Read DEMO_PASSWORD locally for demo login; do not commit or share it."
)
