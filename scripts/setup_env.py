"""Create local configuration without displaying secrets or replacing existing files."""
from pathlib import Path
import os
import secrets

ROOT = Path(__file__).resolve().parents[1]
SECRET_NAMES = {"JWT_SECRET_KEY", "DEVELOPER_PASSWORD", "DB_PASSWORD", "MYSQL_ROOT_PASSWORD"}


def main() -> int:
    target = ROOT / ".env"
    lines = (ROOT / ".env.example").read_text(encoding="utf-8").splitlines()
    configured = []
    for line in lines:
        name = line.partition("=")[0]
        configured.append(f"{name}={secrets.token_urlsafe(48)}" if name in SECRET_NAMES else line)
    try:
        # O_EXCL also protects against concurrent runs; 0o600 limits permissions on Unix.
        descriptor = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError:
        print(".env already exists; no files were changed.")
        return 0
    with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
        handle.write("\n".join(configured) + "\n")
    print("Created ignored .env with unique credentials. Read it locally when signing in.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
