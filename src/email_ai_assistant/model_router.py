import os

MODEL_ROUTES = {
    "triage": {
        "env": "AI_TRIAGE_MODEL",
        "fallback": "configurable-fast-triage-model",
        "purpose": "Classify email category, priority, usefulness, and required action.",
    },
    "summary": {
        "env": "AI_SUMMARY_MODEL",
        "fallback": "configurable-long-context-summary-model",
        "purpose": "Summarize long, study, finance, HR, and detailed email bodies.",
    },
    "draft": {
        "env": "AI_DRAFT_MODEL",
        "fallback": "configurable-draft-writing-model",
        "purpose": "Write reply drafts in the user's preferred tone.",
    },
    "safety": {
        "env": "AI_SAFETY_MODEL",
        "fallback": "configurable-safety-review-model",
        "purpose": "Check send, trash, alert, and sensitive-data actions before execution.",
    },
    "memory": {
        "env": "AI_EMBEDDING_MODEL",
        "fallback": "configurable-memory-embedding-model",
        "purpose": "Learn sender/category/tone preferences from daily feedback.",
    },
}


def resolve_model_routes(env=None):
    env = env or os.environ
    return {
        task: {
            "task": task,
            "model": env.get(route["env"], route["fallback"]),
            "configurableBy": route["env"],
            "purpose": route["purpose"],
        }
        for task, route in MODEL_ROUTES.items()
    }
