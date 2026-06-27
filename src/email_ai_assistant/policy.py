from .categories import CLEANABLE_CATEGORIES, PROTECTED_CATEGORIES

ACTIONS = {
    "review": "review",
    "summarize": "summarize",
    "draft_reply": "draft_reply",
    "alert_user": "alert_user",
    "trash_review": "trash_review",
    "archive_candidate": "archive_candidate",
}


def build_action_policy(analysis):
    checks = []
    category = analysis["category"]

    if analysis["replyRequired"]:
        checks.append("Draft only. Sending requires user approval.")

    if category in CLEANABLE_CATEGORIES and not analysis["important"]:
        checks.append("Can be selected for one-shot Trash cleanup.")

    if category == "low_value_loan_offer":
        checks.append("Recommend trash review. Do not permanently delete automatically.")

    if category in PROTECTED_CATEGORIES or analysis["important"]:
        checks.append("Protected from bulk cleanup and auto-delete.")

    if analysis["alert"]["shouldNotify"]:
        checks.append("Notify user through in-app/browser notification.")

    if not checks:
        checks.append("No high-risk action detected.")

    return {
        "canAutoSend": False,
        "canPermanentDelete": False,
        "canRecommendTrash": category in CLEANABLE_CATEGORIES and not analysis["important"],
        "needsHumanApproval": analysis["replyRequired"] or category in CLEANABLE_CATEGORIES,
        "checks": checks,
    }


def can_bulk_trash(analysis):
    return build_action_policy(analysis)["canRecommendTrash"]
