CATEGORY_META = {
    "important_finance": {
        "label": "Finance",
        "priority": 90,
        "tone": "careful",
        "description": "Banking, salary, account, tax, insurance, invoices, and financial documents.",
    },
    "company_hr": {
        "label": "Company / HR",
        "priority": 88,
        "tone": "professional",
        "description": "Employer, HR, payroll, benefits, manager, team, and workplace requests.",
    },
    "career_recruiter": {
        "label": "Career / Recruiter",
        "priority": 92,
        "tone": "professional",
        "description": "Recruiter outreach, interview steps, job opportunities, and CV or resume requests.",
    },
    "home_renewal": {
        "label": "Home / Renewal",
        "priority": 82,
        "tone": "practical",
        "description": "Rent, maintenance, utility, subscription, policy, and other renewal deadlines.",
    },
    "study_summary": {
        "label": "Study / Knowledge",
        "priority": 62,
        "tone": "clear",
        "description": "Long-form learning, newsletters, research, courses, and technical updates.",
    },
    "marketing_promotion": {
        "label": "Marketing",
        "priority": 30,
        "tone": "brief",
        "description": "Offers, sales, product launches, and generic promotions.",
    },
    "low_value_loan_offer": {
        "label": "Loan / Spam",
        "priority": 18,
        "tone": "brief",
        "description": "Low-value loan offers, pre-approved credit pitches, and repeated finance promotions.",
    },
    "social_update": {
        "label": "Social",
        "priority": 25,
        "tone": "brief",
        "description": "Social network, community, like, follow, and generic activity updates.",
    },
    "personal": {
        "label": "Personal",
        "priority": 70,
        "tone": "warm",
        "description": "Direct mail from known people.",
    },
    "needs_review": {
        "label": "Needs Review",
        "priority": 50,
        "tone": "neutral",
        "description": "Uncertain messages that need user review.",
    },
}

CLEANABLE_CATEGORIES = {"low_value_loan_offer", "marketing_promotion", "social_update"}
PROTECTED_CATEGORIES = {"important_finance", "company_hr", "career_recruiter", "home_renewal", "personal"}


def get_category_meta(category):
    return CATEGORY_META.get(category, CATEGORY_META["needs_review"])
