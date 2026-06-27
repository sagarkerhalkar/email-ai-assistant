SOURCE_OF_TRUTH_REQUIREMENTS = (
    "Check every connected email and use the full message context for decisions.",
    "Categorize mail into finance, company/HR, career/recruiter, home/renewal, study, marketing, low-value loan/spam, social, personal, or needs-review.",
    "Summarize long, study, newsletter, and detailed mail when the user opens it.",
    "Detect important messages that need a reply and prepare a draft response.",
    "Never send an email until the user explicitly approves it.",
    "Support bulk selection and one-shot cleanup of unnecessary mail while protecting important mail.",
    "Alert the user for recruiter CV requests, interview actions, urgent HR/company mail, salary/account issues, and renewal deadlines.",
    "Use in-app/browser notifications by default because WhatsApp Business is not required.",
    "Recommend low-value loan and irrelevant promotional mail for trash review, but do not permanently delete automatically.",
    "Learn from user corrections, approvals, rejected drafts, category changes, and delete/archive choices day by day.",
    "Keep model choices configurable by task: triage, summary, draft, safety, and memory.",
    "Maintain CI, tests, debugging support, and responsive layouts for mobile, tablet, laptop, desktop, and major browsers.",
)


def get_requirement_snapshot():
    return {
        "name": "Email AI Assistant",
        "version": "0.1.0",
        "requirements": list(SOURCE_OF_TRUTH_REQUIREMENTS),
    }
