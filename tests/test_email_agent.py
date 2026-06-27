import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from email_ai_assistant.agent import analyze_email, analyze_mailbox
from email_ai_assistant.policy import can_bulk_trash
from email_ai_assistant.sample_emails import get_sample_emails


class EmailAgentTests(unittest.TestCase):
    def test_loan_promotion_is_bulk_cleanable_without_being_important(self):
        email = next(item for item in get_sample_emails() if item["id"] == "mail-001")
        analysis = analyze_email(email)

        self.assertEqual(analysis["category"], "low_value_loan_offer")
        self.assertEqual(analysis["recommendedAction"], "trash_review")
        self.assertFalse(analysis["important"])
        self.assertTrue(can_bulk_trash(analysis))
        self.assertRegex(" ".join(analysis["policyNotes"]), r"not permanent deletion")

    def test_recruiter_cv_request_is_important_alertable_and_gets_draft(self):
        email = next(item for item in get_sample_emails() if item["id"] == "mail-002")
        analysis = analyze_email(email)

        self.assertEqual(analysis["category"], "career_recruiter")
        self.assertTrue(analysis["important"])
        self.assertTrue(analysis["replyRequired"])
        self.assertTrue(analysis["alert"]["shouldNotify"])
        self.assertEqual(analysis["alert"]["channel"], "in_app")
        self.assertRegex(analysis["draft"], r"latest CV")
        self.assertFalse(can_bulk_trash(analysis))
        self.assertTrue(analysis["attachmentRequest"]["required"])
        self.assertIn("cv", analysis["attachmentRequest"]["hints"])

    def test_long_study_mail_receives_a_long_form_summary(self):
        email = next(item for item in get_sample_emails() if item["id"] == "mail-004")
        analysis = analyze_email(email)

        self.assertEqual(analysis["category"], "study_summary")
        self.assertTrue(analysis["longForm"])
        self.assertEqual(analysis["summary"]["detailLevel"], "long-form")
        self.assertGreaterEqual(len(analysis["summary"]["bullets"]), 3)

    def test_mailbox_analysis_returns_counts_alerts_and_trash_review_queues(self):
        result = analyze_mailbox(get_sample_emails())

        self.assertEqual(len(result["emails"]), 7)
        self.assertTrue(any(item["category"] == "career_recruiter" for item in result["alerts"]))
        self.assertTrue(any(item["category"] == "low_value_loan_offer" for item in result["trashReview"]))
        self.assertIsInstance(result["models"]["triage"]["model"], str)


if __name__ == "__main__":
    unittest.main()
