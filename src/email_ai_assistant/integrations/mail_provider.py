import base64
import json
import mimetypes
import secrets
import time
from datetime import datetime, timezone
from email.message import EmailMessage
from email.utils import parseaddr
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from ..config import resolve_private_path
from ..sample_emails import get_sample_emails

DEFAULT_ACTION_STATE_PATH = Path(__file__).resolve().parents[3] / "data" / "mail-actions.json"
GMAIL_API_BASE = "https://gmail.googleapis.com/gmail/v1"
GMAIL_SCOPES = ("https://www.googleapis.com/auth/gmail.modify",)


class SampleMailProvider:
    provider_name = "sample"

    def __init__(self, state_path=DEFAULT_ACTION_STATE_PATH):
        self.state_path = Path(state_path)

    def list_messages(self):
        state = self._load_state()
        trashed_ids = set(state.get("trashedIds", []))
        return [email for email in get_sample_emails() if email["id"] not in trashed_ids]

    def send_reply(self, email_id, draft, approved, attachment_paths=None):
        if not approved:
            return {
                "sent": False,
                "status": "approval_required",
                "message": "The draft was not sent because approval was not provided.",
            }

        attachment_names = [Path(path).name for path in attachment_paths or []]
        return {
            "sent": True,
            "status": "mock_sent",
            "emailId": email_id,
            "preview": draft,
            "attachments": attachment_names,
            "message": "Mock provider accepted the approved draft. Complete Gmail OAuth for real sending.",
        }

    def bulk_move_to_trash(self, email_ids, approved):
        if not approved:
            return {
                "moved": False,
                "status": "approval_required",
                "movedIds": [],
                "message": "Bulk cleanup requires explicit approval.",
            }

        state = self._load_state()
        existing = set(state.get("trashedIds", []))
        moved_ids = sorted(set(email_ids) - existing)
        state["trashedIds"] = sorted(existing | set(moved_ids))
        state.setdefault("trashEvents", []).append(
            {
                "createdAt": datetime.now(timezone.utc).isoformat(),
                "movedIds": moved_ids,
            }
        )
        self._save_state(state)

        return {
            "moved": True,
            "status": "mock_trashed",
            "movedIds": moved_ids,
            "message": f"Moved {len(moved_ids)} selected message(s) to Trash. Permanent deletion is disabled.",
        }

    def _load_state(self):
        if not self.state_path.exists():
            return {"trashedIds": [], "trashEvents": []}
        return json.loads(self.state_path.read_text(encoding="utf-8"))

    def _save_state(self, state):
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        self.state_path.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")


class GmailOAuthClient:
    def __init__(self, settings):
        self.settings = settings
        self.credentials_path = resolve_private_path(settings["gmailCredentialsPath"])
        self.token_path = resolve_private_path(settings["gmailTokenPath"])
        self.state_path = self.token_path.with_suffix(".state")

    def has_credentials(self):
        return self.credentials_path.exists()

    def is_connected(self):
        token = self._load_token()
        return bool(token.get("refresh_token") or token.get("access_token"))

    def build_auth_url(self):
        client = self._client_config()
        state = secrets.token_urlsafe(32)
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        self.state_path.write_text(state, encoding="utf-8")
        params = {
            "client_id": client["client_id"],
            "redirect_uri": self.settings["gmailRedirectUri"],
            "response_type": "code",
            "scope": " ".join(GMAIL_SCOPES),
            "access_type": "offline",
            "prompt": "consent",
            "state": state,
        }
        auth_uri = client.get("auth_uri", "https://accounts.google.com/o/oauth2/v2/auth")
        return f"{auth_uri}?{urlencode(params)}"

    def exchange_code(self, code, state):
        if self.state_path.exists():
            expected_state = self.state_path.read_text(encoding="utf-8")
            if state != expected_state:
                raise ValueError("OAuth state did not match. Please start Gmail connect again.")

        client = self._client_config()
        payload = {
            "code": code,
            "client_id": client["client_id"],
            "client_secret": client.get("client_secret", ""),
            "redirect_uri": self.settings["gmailRedirectUri"],
            "grant_type": "authorization_code",
        }
        token = self._post_form(client.get("token_uri", "https://oauth2.googleapis.com/token"), payload)
        self._save_token(token)
        return token

    def get_access_token(self):
        token = self._load_token()
        if not token:
            raise ValueError("Gmail is not connected yet.")

        if token.get("access_token") and token.get("expires_at", 0) > time.time() + 60:
            return token["access_token"]

        if not token.get("refresh_token"):
            raise ValueError("Gmail token has expired and no refresh token is available.")

        client = self._client_config()
        refreshed = self._post_form(
            client.get("token_uri", "https://oauth2.googleapis.com/token"),
            {
                "client_id": client["client_id"],
                "client_secret": client.get("client_secret", ""),
                "refresh_token": token["refresh_token"],
                "grant_type": "refresh_token",
            },
        )
        token.update(refreshed)
        self._save_token(token)
        return token["access_token"]

    def request_json(self, method, path, payload=None, query=None):
        url = f"{GMAIL_API_BASE}{path}"
        if query:
            url = f"{url}?{urlencode(query)}"

        data = None
        headers = {"Authorization": f"Bearer {self.get_access_token()}"}
        if payload is not None:
            data = json.dumps(payload).encode("utf-8")
            headers["Content-Type"] = "application/json"

        request = Request(url, data=data, headers=headers, method=method)
        with urlopen(request, timeout=30) as response:
            raw = response.read().decode("utf-8")
            return json.loads(raw) if raw else {}

    def _client_config(self):
        if not self.credentials_path.exists():
            raise FileNotFoundError(f"Gmail credentials file not found: {self.credentials_path}")
        data = json.loads(self.credentials_path.read_text(encoding="utf-8"))
        return data.get("installed") or data.get("web") or data

    def _load_token(self):
        if not self.token_path.exists():
            return {}
        return json.loads(self.token_path.read_text(encoding="utf-8"))

    def _save_token(self, token):
        if token.get("expires_in"):
            token["expires_at"] = time.time() + int(token["expires_in"])
        self.token_path.parent.mkdir(parents=True, exist_ok=True)
        self.token_path.write_text(json.dumps(token, indent=2) + "\n", encoding="utf-8")

    def _post_form(self, url, payload):
        data = urlencode(payload).encode("utf-8")
        request = Request(url, data=data, headers={"Content-Type": "application/x-www-form-urlencoded"}, method="POST")
        with urlopen(request, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))


class GmailMailProvider:
    provider_name = "gmail"

    def __init__(self, settings):
        self.settings = settings
        self.oauth = GmailOAuthClient(settings)

    def list_messages(self, max_results=25):
        listing = self.oauth.request_json(
            "GET",
            "/users/me/messages",
            query={"maxResults": max_results, "q": "-in:trash"},
        )
        messages = listing.get("messages", [])
        return [self._convert_message(self.get_message(item["id"])) for item in messages]

    def get_message(self, email_id):
        return self.oauth.request_json("GET", f"/users/me/messages/{email_id}", query={"format": "full"})

    def send_reply(self, email_id, draft, approved, attachment_paths=None):
        if not approved:
            return {
                "sent": False,
                "status": "approval_required",
                "message": "The draft was not sent because approval was not provided.",
            }

        original = self.get_message(email_id)
        headers = _headers(original)
        recipient = parseaddr(headers.get("From", ""))[1] or headers.get("From", "")
        subject = headers.get("Subject", "")
        reply_subject = subject if subject.lower().startswith("re:") else f"Re: {subject}"

        message = EmailMessage()
        message["To"] = recipient
        message["Subject"] = reply_subject
        if headers.get("Message-ID"):
            message["In-Reply-To"] = headers["Message-ID"]
            message["References"] = headers["Message-ID"]
        message.set_content(draft)

        attached = []
        for path in attachment_paths or []:
            file_path = Path(path)
            if not file_path.exists() or not file_path.is_file():
                continue
            content_type = mimetypes.guess_type(str(file_path))[0] or "application/octet-stream"
            maintype, subtype = content_type.split("/", 1)
            message.add_attachment(
                file_path.read_bytes(),
                maintype=maintype,
                subtype=subtype,
                filename=file_path.name,
            )
            attached.append(file_path.name)

        raw = base64.urlsafe_b64encode(message.as_bytes()).decode("ascii")
        result = self.oauth.request_json(
            "POST",
            "/users/me/messages/send",
            payload={"raw": raw, "threadId": original.get("threadId")},
        )

        return {
            "sent": True,
            "status": "gmail_sent",
            "emailId": email_id,
            "gmailMessageId": result.get("id"),
            "attachments": attached,
            "message": f"Sent through Gmail with {len(attached)} attachment(s).",
        }

    def bulk_move_to_trash(self, email_ids, approved):
        if not approved:
            return {
                "moved": False,
                "status": "approval_required",
                "movedIds": [],
                "message": "Bulk cleanup requires explicit approval.",
            }

        moved = []
        for email_id in email_ids:
            self.oauth.request_json("POST", f"/users/me/messages/{email_id}/trash", payload={})
            moved.append(email_id)

        return {
            "moved": True,
            "status": "gmail_trashed",
            "movedIds": moved,
            "message": f"Moved {len(moved)} selected Gmail message(s) to Trash.",
        }

    def search_and_save_attachments(self, query="filename:pdf (cv OR resume)", max_results=10):
        attachments_dir = resolve_private_path(self.settings["draftAttachmentsDir"])
        attachments_dir.mkdir(parents=True, exist_ok=True)
        listing = self.oauth.request_json(
            "GET",
            "/users/me/messages",
            query={"maxResults": max_results, "q": query},
        )
        saved = []
        for item in listing.get("messages", []):
            message = self.get_message(item["id"])
            for part in _walk_parts(message.get("payload", {})):
                filename = part.get("filename") or ""
                attachment_id = part.get("body", {}).get("attachmentId")
                if not filename or not attachment_id:
                    continue
                attachment = self.oauth.request_json(
                    "GET",
                    f"/users/me/messages/{item['id']}/attachments/{attachment_id}",
                )
                data = _base64url_decode(attachment.get("data", ""))
                target = _safe_attachment_path(attachments_dir, filename)
                target.write_bytes(data)
                saved.append({"name": target.name, "path": str(target), "sourceEmailId": item["id"]})
        return saved

    def _convert_message(self, message):
        headers = _headers(message)
        body = _message_body(message.get("payload", {})) or message.get("snippet", "")
        return {
            "id": message["id"],
            "threadId": message.get("threadId"),
            "from": headers.get("From", ""),
            "senderName": parseaddr(headers.get("From", ""))[0] or headers.get("From", ""),
            "subject": headers.get("Subject", "(no subject)"),
            "receivedAt": _gmail_date(headers.get("Date")),
            "body": body,
        }


def build_mail_provider(settings):
    oauth = GmailOAuthClient(settings)
    if settings["gmailEnabled"] and oauth.has_credentials() and oauth.is_connected():
        return GmailMailProvider(settings)
    return SampleMailProvider()


def gmail_status(settings):
    oauth = GmailOAuthClient(settings)
    return {
        "enabled": settings["gmailEnabled"],
        "credentialsPresent": oauth.has_credentials(),
        "connected": oauth.is_connected() if oauth.has_credentials() else False,
        "authUrlAvailable": settings["gmailEnabled"] and oauth.has_credentials(),
    }


def list_local_attachments(settings, attachment_request=None):
    files = []
    cv_path = resolve_private_path(settings["cvFilePath"])
    if cv_path.exists() and cv_path.is_file():
        files.append({"name": cv_path.name, "path": str(cv_path), "kind": "cv", "suggested": False})

    attachments_dir = resolve_private_path(settings["draftAttachmentsDir"])
    if attachments_dir.exists():
        for path in sorted(attachments_dir.iterdir()):
            if path.is_file():
                files.append({"name": path.name, "path": str(path), "kind": "attachment", "suggested": False})

    hints = set((attachment_request or {}).get("hints", []))
    for item in files:
        if item["kind"] == "cv" and "cv" in hints:
            item["suggested"] = True
        elif hints and item["kind"] == "attachment":
            item["suggested"] = True

    return files


def suggested_attachment_paths(settings, attachment_request=None):
    return [
        item["path"]
        for item in list_local_attachments(settings, attachment_request)
        if item["suggested"]
    ]


def _headers(message):
    return {
        item.get("name", ""): item.get("value", "")
        for item in message.get("payload", {}).get("headers", [])
    }


def _message_body(payload):
    if payload.get("mimeType") == "text/plain" and payload.get("body", {}).get("data"):
        return _base64url_decode(payload["body"]["data"]).decode("utf-8", errors="replace")

    for part in payload.get("parts", []) or []:
        text = _message_body(part)
        if text:
            return text
    return ""


def _walk_parts(payload):
    yield payload
    for part in payload.get("parts", []) or []:
        yield from _walk_parts(part)


def _base64url_decode(value):
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(f"{value}{padding}")


def _safe_attachment_path(directory, filename):
    clean = "".join(char if char.isalnum() or char in "._- " else "_" for char in filename).strip()
    target = directory / (clean or "attachment")
    if not target.exists():
        return target

    stem = target.stem
    suffix = target.suffix
    for index in range(1, 1000):
        candidate = directory / f"{stem}-{index}{suffix}"
        if not candidate.exists():
            return candidate
    raise ValueError("Too many duplicate attachment names.")


def _gmail_date(value):
    if not value:
        return datetime.now(timezone.utc).isoformat()
    try:
        from email.utils import parsedate_to_datetime

        return parsedate_to_datetime(value).isoformat()
    except Exception:
        return datetime.now(timezone.utc).isoformat()
