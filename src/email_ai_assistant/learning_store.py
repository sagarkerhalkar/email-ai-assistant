import json
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_STORE_PATH = Path(__file__).resolve().parents[2] / "data" / "agent-memory.json"


def create_empty_memory():
    return {
        "version": 1,
        "categoryOverrides": {},
        "importantSenders": [],
        "blockedSenders": [],
        "preferredTone": "professional and concise",
        "feedback": [],
        "bulkCleanupHistory": [],
    }


def load_memory(store_path=DEFAULT_STORE_PATH):
    path = Path(store_path)
    if not path.exists():
        return create_empty_memory()
    return json.loads(path.read_text(encoding="utf-8"))


def save_memory(memory, store_path=DEFAULT_STORE_PATH):
    path = Path(store_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(memory, indent=2) + "\n", encoding="utf-8")
    return memory


def record_feedback(feedback, store_path=DEFAULT_STORE_PATH):
    memory = load_memory(store_path)
    entry = {
        "id": f"feedback-{int(datetime.now(timezone.utc).timestamp() * 1000)}",
        "createdAt": datetime.now(timezone.utc).isoformat(),
        "emailId": feedback.get("emailId"),
        "sender": feedback.get("sender"),
        "category": feedback.get("category"),
        "correctedCategory": feedback.get("correctedCategory"),
        "draftApproved": bool(feedback.get("draftApproved")),
        "draftRejected": bool(feedback.get("draftRejected")),
        "notes": feedback.get("notes", ""),
    }

    memory["feedback"].append(entry)

    if entry["sender"] and entry["correctedCategory"]:
        memory["categoryOverrides"][entry["sender"]] = entry["correctedCategory"]

    return save_memory(memory, store_path)


def record_bulk_cleanup(moved_ids, blocked_ids, store_path=DEFAULT_STORE_PATH):
    memory = load_memory(store_path)
    memory["bulkCleanupHistory"].append(
        {
            "createdAt": datetime.now(timezone.utc).isoformat(),
            "movedIds": moved_ids,
            "blockedIds": blocked_ids,
        }
    )
    return save_memory(memory, store_path)
