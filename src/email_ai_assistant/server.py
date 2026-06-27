import json
import mimetypes
import os
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse

from .agent import analyze_mailbox
from .config import get_settings
from .learning_store import load_memory, record_bulk_cleanup, record_feedback
from .policy import build_action_policy, can_bulk_trash
from .requirements import get_requirement_snapshot
from .integrations.mail_provider import (
    GmailMailProvider,
    GmailOAuthClient,
    build_mail_provider,
    gmail_status,
    list_local_attachments,
    suggested_attachment_paths,
)
from .integrations.notification_provider import InAppNotificationProvider

ROOT = Path(__file__).resolve().parents[2]
PUBLIC_DIR = ROOT / "public"

notification_provider = InAppNotificationProvider()


class EmailAssistantHandler(BaseHTTPRequestHandler):
    server_version = "EmailAIAssistant/0.1"

    def do_GET(self):
        parsed = urlparse(self.path)
        query = parse_query(parsed.query)

        if query.get("code") and query.get("state") and parsed.path in {"/", "/auth/google/callback"}:
            GmailOAuthClient(get_settings()).exchange_code(query.get("code", ""), query.get("state", ""))
            self.send_html("<h1>Gmail connected</h1><p>You can close this tab and return to Email AI Assistant.</p>")
            return

        if query.get("error") and parsed.path in {"/", "/auth/google/callback"}:
            self.send_html(f"<h1>Gmail connection failed</h1><p>{query['error']}</p>", status=400)
            return

        if parsed.path == "/api/health":
            self.send_json({"ok": True, "service": "email-ai-assistant-python"})
            return

        if parsed.path == "/api/requirements":
            self.send_json(get_requirement_snapshot())
            return

        if parsed.path == "/api/emails":
            self.send_json(build_mailbox_payload())
            return

        if parsed.path == "/api/gmail/status":
            self.send_json(gmail_status(get_settings()))
            return

        if parsed.path == "/api/gmail/auth-url":
            self.send_json({"authUrl": GmailOAuthClient(get_settings()).build_auth_url()})
            return

        if parsed.path == "/api/attachments":
            self.send_json({"attachments": list_local_attachments(get_settings())})
            return

        if parsed.path == "/auth/google/callback":
            self.send_html("<h1>Waiting for Gmail</h1><p>Start from the Connect Gmail button in the app.</p>")
            return

        self.serve_static(parsed.path)

    def do_POST(self):
        parsed = urlparse(self.path)
        body = self.read_json()

        if parsed.path == "/api/feedback":
            memory = record_feedback(body)
            self.send_json({"ok": True, "memory": memory})
            return

        if parsed.path == "/api/send-draft":
            settings = get_settings()
            attachments = body.get("attachmentPaths")
            if attachments is None:
                attachments = suggested_attachment_paths(settings, body.get("attachmentRequest"))
            provider = build_mail_provider(settings)
            result = provider.send_reply(
                email_id=body.get("emailId"),
                draft=body.get("draft", ""),
                approved=body.get("approved") is True,
                attachment_paths=attachments,
            )
            self.send_json(result, status=200 if result["sent"] else 409)
            return

        if parsed.path == "/api/notify":
            result = notification_provider.notify(body.get("alert"))
            self.send_json(result)
            return

        if parsed.path == "/api/bulk-trash":
            result = bulk_trash(body)
            self.send_json(result, status=200 if result["moved"] else 409)
            return

        if parsed.path == "/api/gmail/find-attachments":
            provider = build_mail_provider(get_settings())
            if not isinstance(provider, GmailMailProvider):
                self.send_json(
                    {"ok": False, "message": "Connect Gmail before searching mail attachments."},
                    status=409,
                )
                return
            query = body.get("query") or "filename:pdf (cv OR resume)"
            saved = provider.search_and_save_attachments(query=query)
            self.send_json({"ok": True, "saved": saved})
            return

        self.send_json({"error": "Not found"}, status=404)

    def serve_static(self, request_path):
        safe_path = "/index.html" if request_path == "/" else unquote(request_path)
        target = (PUBLIC_DIR / safe_path.lstrip("/")).resolve()

        if not str(target).startswith(str(PUBLIC_DIR.resolve())):
            self.send_json({"error": "Forbidden"}, status=403)
            return

        if not target.exists() or not target.is_file():
            self.send_json({"error": "Not found"}, status=404)
            return

        content_type = mimetypes.guess_type(str(target))[0] or "application/octet-stream"
        data = target.read_bytes()
        self.send_response(200)
        self.send_header("content-type", content_type)
        self.send_header("content-length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def read_json(self):
        length = int(self.headers.get("content-length", "0"))
        if length > 1_000_000:
            raise ValueError("Request body too large")
        raw = self.rfile.read(length).decode("utf-8") if length else "{}"
        return json.loads(raw or "{}")

    def send_json(self, payload, status=200):
        data = json.dumps(payload, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("content-type", "application/json; charset=utf-8")
        self.send_header("content-length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def send_html(self, html, status=200):
        data = f"<!doctype html><html><body>{html}</body></html>".encode("utf-8")
        self.send_response(status)
        self.send_header("content-type", "text/html; charset=utf-8")
        self.send_header("content-length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, format, *args):
        safe_print(f"{self.address_string()} - {format % args}")


def build_mailbox_payload():
    settings = get_settings()
    memory = load_memory()
    provider = build_mail_provider(settings)
    emails = provider.list_messages()
    payload = analyze_mailbox(emails, memory=memory, env=os.environ)
    payload["account"] = {
        "email": settings["mailboxEmail"],
        "provider": provider.provider_name,
        "gmail": gmail_status(settings),
    }
    payload["emails"] = [
        {
            **email,
            "actionPolicy": build_action_policy(email),
            "suggestedAttachments": list_local_attachments(settings, email.get("attachmentRequest")),
        }
        for email in payload["emails"]
    ]
    payload["attachments"] = list_local_attachments(settings)
    return payload


def bulk_trash(body):
    approved = body.get("approved") is True
    requested_ids = set(body.get("emailIds") or [])
    provider = build_mail_provider(get_settings())
    payload = build_mailbox_payload()
    by_id = {email["id"]: email for email in payload["emails"]}

    allowed = sorted(
        email_id
        for email_id in requested_ids
        if email_id in by_id and can_bulk_trash(by_id[email_id])
    )
    blocked = sorted(email_id for email_id in requested_ids if email_id not in set(allowed))

    if not allowed:
        return {
            "moved": False,
            "status": "nothing_cleanable",
            "movedIds": [],
            "blockedIds": blocked,
            "message": "No selected messages are safe for bulk cleanup.",
        }

    result = provider.bulk_move_to_trash(allowed, approved=approved)
    result["blockedIds"] = blocked
    if result.get("moved"):
        record_bulk_cleanup(result.get("movedIds", []), blocked)
    if blocked:
        result["message"] += f" Protected or uncertain messages skipped: {len(blocked)}."
    return result


def run():
    port = get_settings()["port"]
    server = ThreadingHTTPServer(("localhost", port), EmailAssistantHandler)
    safe_print(f"Email AI Assistant running at http://localhost:{port}")
    server.serve_forever()


def safe_print(message):
    if sys.stdout:
        print(message)


def parse_query(raw_query):
    from urllib.parse import parse_qs

    parsed = parse_qs(raw_query, keep_blank_values=True)
    return {key: values[-1] if values else "" for key, values in parsed.items()}
