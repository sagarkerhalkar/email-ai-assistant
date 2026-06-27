import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_ENV_PATH = ROOT / ".env"


def load_env_file(path=DEFAULT_ENV_PATH):
    env_path = Path(path)
    if not env_path.exists():
        return {}

    loaded = {}
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)
        loaded[key] = value
    return loaded


def get_settings():
    load_env_file()
    return {
        "mailboxEmail": os.environ.get("MAILBOX_EMAIL", ""),
        "alertProvider": os.environ.get("ALERT_PROVIDER", "in_app"),
        "port": int(os.environ.get("PORT", "4173")),
        "gmailEnabled": os.environ.get("GMAIL_ENABLED", "false").lower() == "true",
        "gmailCredentialsPath": os.environ.get("GMAIL_CREDENTIALS_PATH", "private/gmail_credentials.json"),
        "gmailTokenPath": os.environ.get("GMAIL_TOKEN_PATH", "private/gmail_token.json"),
        "gmailRedirectUri": os.environ.get("GMAIL_REDIRECT_URI", "http://localhost:4173/"),
        "cvFilePath": os.environ.get("CV_FILE_PATH", "private/cv.pdf"),
        "draftAttachmentsDir": os.environ.get("DRAFT_ATTACHMENTS_DIR", "private/attachments"),
    }


def resolve_private_path(path_value):
    path = Path(path_value)
    if not path.is_absolute():
        path = ROOT / path
    return path.resolve()
