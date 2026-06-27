import re
from datetime import datetime, timezone

from .categories import CATEGORY_META, get_category_meta
from .model_router import resolve_model_routes
from .policy import ACTIONS

IMPORTANT_SENDER_PATTERNS = (
    re.compile(r"payroll", re.I),
    re.compile(r"\bhr\b", re.I),
    re.compile(r"recruit", re.I),
    re.compile(r"talent", re.I),
    re.compile(r"bank", re.I),
    re.compile(r"insurance", re.I),
    re.compile(r"renewal", re.I),
)

CATEGORY_PATTERNS = (
    (
        "career_recruiter",
        (
            re.compile(r"\brecruit(er|ment)?\b", re.I),
            re.compile(r"\bresume\b", re.I),
            re.compile(r"\bcv\b", re.I),
            re.compile(r"\binterview\b", re.I),
            re.compile(r"\bhiring\b", re.I),
            re.compile(r"\bjob opportunity\b", re.I),
            re.compile(r"\brole\b", re.I),
        ),
    ),
    (
        "company_hr",
        (
            re.compile(r"\bhr\b", re.I),
            re.compile(r"\bpayroll\b", re.I),
            re.compile(r"\bemployer\b", re.I),
            re.compile(r"\bemployee\b", re.I),
            re.compile(r"\bmanager\b", re.I),
            re.compile(r"\bbenefits?\b", re.I),
            re.compile(r"\bpolicy\b", re.I),
            re.compile(r"\bteam\b", re.I),
        ),
    ),
    (
        "important_finance",
        (
            re.compile(r"\bsalary\b", re.I),
            re.compile(r"\bpayslip\b", re.I),
            re.compile(r"\bbank\b", re.I),
            re.compile(r"\baccount\b", re.I),
            re.compile(r"\btax\b", re.I),
            re.compile(r"\binsurance\b", re.I),
            re.compile(r"\binvoice\b", re.I),
            re.compile(r"\bstatement\b", re.I),
            re.compile(r"\bkyc\b", re.I),
            re.compile(r"\btransaction\b", re.I),
        ),
    ),
    (
        "home_renewal",
        (
            re.compile(r"\bhome\b", re.I),
            re.compile(r"\brent\b", re.I),
            re.compile(r"\bmaintenance\b", re.I),
            re.compile(r"\brenew(al)?\b", re.I),
            re.compile(r"\bdue\b", re.I),
            re.compile(r"\belectricity\b", re.I),
            re.compile(r"\binternet\b", re.I),
            re.compile(r"\bsubscription\b", re.I),
            re.compile(r"\bexpiry\b", re.I),
        ),
    ),
    (
        "low_value_loan_offer",
        (
            re.compile(r"\bpre-approved\b", re.I),
            re.compile(r"\bpersonal loan\b", re.I),
            re.compile(r"\binstant loan\b", re.I),
            re.compile(r"\bcredit card offer\b", re.I),
            re.compile(r"\bprocessing fee\b", re.I),
            re.compile(r"\bemi\b", re.I),
            re.compile(r"\bloan offer\b", re.I),
        ),
    ),
    (
        "study_summary",
        (
            re.compile(r"\bstudy\b", re.I),
            re.compile(r"\bguide\b", re.I),
            re.compile(r"\bresearch\b", re.I),
            re.compile(r"\bcourse\b", re.I),
            re.compile(r"\btutorial\b", re.I),
            re.compile(r"\bnewsletter\b", re.I),
            re.compile(r"\bengineering\b", re.I),
            re.compile(r"\blearn\b", re.I),
        ),
    ),
    (
        "marketing_promotion",
        (
            re.compile(r"\boffer\b", re.I),
            re.compile(r"\bsale\b", re.I),
            re.compile(r"\bdiscount\b", re.I),
            re.compile(r"\bpromo", re.I),
            re.compile(r"\bdeal\b", re.I),
            re.compile(r"\bunsubscribe\b", re.I),
            re.compile(r"\blimited period\b", re.I),
        ),
    ),
    (
        "social_update",
        (
            re.compile(r"\bsocial\b", re.I),
            re.compile(r"\bprofile views?\b", re.I),
            re.compile(r"\blikes?\b", re.I),
            re.compile(r"\breactions?\b", re.I),
            re.compile(r"\bfollowers?\b", re.I),
            re.compile(r"\bnotifications?\b", re.I),
        ),
    ),
)

REPLY_PATTERNS = (
    re.compile(r"\bplease share\b", re.I),
    re.compile(r"\bcould you\b", re.I),
    re.compile(r"\bplease confirm\b", re.I),
    re.compile(r"\breply\b", re.I),
    re.compile(r"\brespond\b", re.I),
    re.compile(r"\bsend (your|me)\b", re.I),
    re.compile(r"\binterested\b", re.I),
    re.compile(r"\bschedule\b", re.I),
)

ATTACHMENT_PATTERNS = (
    ("cv", re.compile(r"\b(cv|resume|curriculum vitae)\b", re.I)),
    ("portfolio", re.compile(r"\bportfolio\b", re.I)),
    ("certificate", re.compile(r"\bcertificate|certification\b", re.I)),
    ("document", re.compile(r"\bdocument|documents|attachment|attachments\b", re.I)),
    ("id_proof", re.compile(r"\bid proof|identity proof|aadhaar|pan card|passport\b", re.I)),
    ("payslip", re.compile(r"\bpayslip|salary slip\b", re.I)),
)

URGENT_PATTERNS = (
    re.compile(r"\btoday\b", re.I),
    re.compile(r"\btomorrow\b", re.I),
    re.compile(r"\bimmediate\b", re.I),
    re.compile(r"\burgent\b", re.I),
    re.compile(r"\bdue\b", re.I),
    re.compile(r"\bdeadline\b", re.I),
    re.compile(r"\bavoid service interruption\b", re.I),
)


def analyze_mailbox(emails, memory=None, env=None):
    model_routes = resolve_model_routes(env)
    analyses = [
        analyze_email(email, memory=memory, model_routes=model_routes)
        for email in emails
    ]
    analyses.sort(key=lambda item: item["priority"], reverse=True)

    counts = {}
    for item in analyses:
        counts[item["category"]] = counts.get(item["category"], 0) + 1

    return {
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "models": model_routes,
        "counts": counts,
        "emails": analyses,
        "alerts": [item for item in analyses if item["alert"]["shouldNotify"]],
        "trashReview": [
            item for item in analyses if item["recommendedAction"] == ACTIONS["trash_review"]
        ],
    }


def analyze_email(email, memory=None, model_routes=None):
    text = normalize_text(
        f"{email.get('subject', '')} {email.get('from', '')} {email.get('senderName', '')} {email.get('body', '')}"
    )
    category = apply_memory_override(email, classify_email(text), memory)
    meta = get_category_meta(category)
    reply_required = detect_reply_required(text, category)
    long_form = is_long_form(email.get("body", ""))
    important = detect_important(email, text, category, reply_required)
    urgency = score_urgency(text)
    priority = score_priority(meta["priority"], urgency, reply_required, important, long_form)
    summary = summarize_email(email, category, long_form)
    attachment_request = detect_attachment_request(text)
    draft = compose_draft(email, category) if reply_required else None
    alert = build_alert(email, category, important, urgency, reply_required)
    recommended_action = choose_recommended_action(
        category, reply_required, long_form, important, alert["shouldNotify"]
    )
    confidence = score_confidence(category, text)

    return {
        **email,
        "category": category,
        "categoryLabel": CATEGORY_META.get(category, CATEGORY_META["needs_review"])["label"],
        "important": important,
        "replyRequired": reply_required,
        "longForm": long_form,
        "priority": priority,
        "confidence": confidence,
        "usefulness": score_usefulness(category, important, long_form),
        "summary": summary,
        "draft": draft,
        "attachmentRequest": attachment_request,
        "alert": alert,
        "recommendedAction": recommended_action,
        "policyNotes": build_policy_notes(category, reply_required, important, alert["shouldNotify"]),
        "modelRouteHints": model_routes or resolve_model_routes(),
    }


def classify_email(text):
    matches = []
    for category, patterns in CATEGORY_PATTERNS:
        score = sum(1 for pattern in patterns if pattern.search(text))
        if score > 0:
            matches.append({"category": category, "score": score})

    if not matches:
        return "needs_review"

    matches.sort(
        key=lambda item: (item["score"], get_category_meta(item["category"])["priority"]),
        reverse=True,
    )

    if any(item["category"] == "career_recruiter" and item["score"] >= 2 for item in matches):
        return "career_recruiter"

    if any(item["category"] == "low_value_loan_offer" and item["score"] >= 2 for item in matches):
        return "low_value_loan_offer"

    return matches[0]["category"]


def summarize_email(email, category, long_form=None):
    long_form = is_long_form(email.get("body", "")) if long_form is None else long_form
    sentences = split_sentences(email.get("body", ""))
    first_points = sentences[: 3 if long_form else 2]
    category_label = get_category_meta(category)["label"]
    action = (
        "A reply or confirmation is likely needed."
        if detect_reply_required(f"{email.get('subject', '')} {email.get('body', '')}", category)
        else "No immediate reply is detected."
    )

    return {
        "headline": f"{category_label}: {email.get('subject', '')}",
        "bullets": first_points or [email.get("body", "")],
        "action": action,
        "detailLevel": "long-form" if long_form else "brief",
    }


def compose_draft(email, category):
    name = friendly_name(email.get("senderName"))

    if category == "career_recruiter":
        return "\n".join(
            [
                f"Hi {name},",
                "",
                "Thank you for reaching out. I am interested in learning more about the role.",
                "Please find my latest CV attached. I would be happy to discuss the opportunity and available interview slots.",
                "",
                "Regards",
            ]
        )

    if category in {"company_hr", "important_finance"}:
        return "\n".join(
            [
                f"Hi {name},",
                "",
                "Thank you for the update. I will review the details and confirm if anything needs correction.",
                "",
                "Regards",
            ]
        )

    return "\n".join(
        [
            f"Hi {name},",
            "",
            "Thanks for the message. I will review this and get back to you.",
            "",
            "Regards",
        ]
    )


def apply_memory_override(email, category, memory):
    if not memory:
        return category
    return memory.get("categoryOverrides", {}).get(email.get("from"), category)


def detect_reply_required(text, category):
    if category == "career_recruiter" and re.search(r"\b(cv|resume|interview|schedule)\b", text, re.I):
        return True
    return any(pattern.search(text) for pattern in REPLY_PATTERNS)


def detect_attachment_request(text):
    hints = [name for name, pattern in ATTACHMENT_PATTERNS if pattern.search(text)]
    return {
        "required": bool(hints),
        "hints": hints,
        "reason": "Requested in email text." if hints else None,
    }


def detect_important(email, text, category, reply_required):
    if category in {"important_finance", "company_hr", "career_recruiter", "home_renewal"}:
        return True
    if reply_required:
        return True
    sender = email.get("from", "")
    return any(pattern.search(sender) or pattern.search(text) for pattern in IMPORTANT_SENDER_PATTERNS)


def score_urgency(text):
    return sum(1 for pattern in URGENT_PATTERNS if pattern.search(text))


def score_priority(base_priority, urgency, reply_required, important, long_form):
    score = base_priority + urgency * 6 + (8 if reply_required else 0) + (5 if important else 0) + (2 if long_form else 0)
    return max(1, min(100, score))


def score_confidence(category, text):
    if category == "needs_review":
        return 0.42
    pattern_group = next((patterns for name, patterns in CATEGORY_PATTERNS if name == category), ())
    matched = sum(1 for pattern in pattern_group if pattern.search(text))
    return max(0.55, min(0.97, 0.58 + matched * 0.1))


def score_usefulness(category, important, long_form):
    if category == "low_value_loan_offer":
        return "low"
    if important:
        return "high"
    if long_form or category == "study_summary":
        return "medium"
    if category in {"marketing_promotion", "social_update"}:
        return "low"
    return "medium"


def build_alert(email, category, important, urgency, reply_required):
    should_notify = category == "career_recruiter" or (important and urgency > 0) or (
        category == "home_renewal" and urgency > 0
    )

    if not should_notify:
        return {"shouldNotify": False, "channel": None, "message": None}

    suffix = " - reply needed" if reply_required else ""
    return {
        "shouldNotify": True,
        "channel": "in_app",
        "message": f"{email.get('senderName') or email.get('from')}: {email.get('subject')}{suffix}",
    }


def choose_recommended_action(category, reply_required, long_form, important, should_notify):
    if category == "low_value_loan_offer":
        return ACTIONS["trash_review"]
    if reply_required:
        return ACTIONS["draft_reply"]
    if should_notify:
        return ACTIONS["alert_user"]
    if long_form:
        return ACTIONS["summarize"]
    if not important and category in {"marketing_promotion", "social_update"}:
        return ACTIONS["archive_candidate"]
    return ACTIONS["review"]


def build_policy_notes(category, reply_required, important, should_notify):
    notes = []
    if reply_required:
        notes.append("Draft prepared. User approval required before sending.")
    if category == "low_value_loan_offer":
        notes.append("Safe action is Trash review, not permanent deletion.")
    if category in {"marketing_promotion", "social_update"} and not important:
        notes.append("Can be bulk-selected for one-shot cleanup.")
    if important:
        notes.append("Important category protected from auto-delete.")
    if should_notify:
        notes.append("Alert through in-app/browser notification.")
    return notes or ["Routine review."]


def is_long_form(body):
    return word_count(body) > 80 or len(split_sentences(body)) >= 5


def word_count(text):
    return len([part for part in normalize_text(text).split(" ") if part])


def split_sentences(text):
    normalized = normalize_text(text)
    if not normalized:
        return []
    return [part.strip() for part in re.split(r"(?<=[.!?])\s+", normalized) if part.strip()]


def normalize_text(text):
    return re.sub(r"\s+", " ", str(text or "")).strip()


def friendly_name(name):
    if not name:
        return "there"
    cleaned = re.sub(r"[^a-z]", "", str(name).split(" ")[0], flags=re.I)
    return cleaned or "there"
