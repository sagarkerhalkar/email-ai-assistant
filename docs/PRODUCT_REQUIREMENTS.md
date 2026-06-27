# Product Requirements: Email AI Assistant

## Source Of Truth

This file captures the durable requirements for the email AI agent. Future features, debugging, CI/CD, tests, and UI work should preserve these requirements unless the product owner changes them explicitly.

## Product Goal

Create a Python-first AI agent or AI application that checks every email, understands its purpose, categorizes it, summarizes long messages, drafts replies when needed, alerts the user for urgent important mail, cleans unnecessary mail in bulk, and only sends email after explicit user approval.

## Core Jobs

1. Read every connected mailbox message.
2. Reference the whole message body, subject, sender, date, links, and detected action requests.
3. Classify the email into meaningful user-focused categories.
4. Identify useful mail versus low-value or promotional mail.
5. Summarize long mail, study mail, newsletters, research updates, and detailed messages when opened.
6. Detect important mail where a reply is needed.
7. Draft a suggested reply for important messages.
8. Send replies only after the user approves.
9. Alert the user through in-app/browser notifications by default because WhatsApp Business is not available.
10. Select unnecessary cleanable mail and move it to Trash in one shot.
11. Attach the user's CV or other approved files to drafts when the email requests them.
12. Learn from user corrections, approvals, deletions, and category changes day by day.

## Required Categories

- Finance: bank account, salary, payslip, tax, insurance, loan account, investment, invoices, bills, statements.
- Company and HR: employer, payroll, HR policy, benefits, manager, team, internal company requests.
- Career and recruiters: job opportunity, interview, recruiter, CV/resume request, hiring update.
- Home and renewals: rent, utilities, maintenance, subscription renewals, insurance renewals, pending due dates.
- Study and knowledge: long-form learning, newsletters, research, courses, technical updates, useful articles.
- Marketing and promotions: offers, sales, product announcements, generic newsletters.
- Low-value loan/spam: personal loan offers, pre-approved loan pitches, repeated finance promotions, irrelevant credit products.
- Social updates: social media notifications, community updates, likes, follows, generic platform activity.
- Personal: direct messages from known people.
- Needs review: anything uncertain.

## Safety Rules

- Never send an email without the user's explicit approval.
- Never permanently delete email automatically.
- Never attach files or send a draft unless the user approves the send action.
- Bulk cleanup moves selected cleanable mail to Trash only.
- Low-value loan, marketing, and social mail can be selected for one-shot cleanup when not important.
- Important finance, salary, HR, home renewal, legal, medical, personal, and recruiter messages must not be bulk-deleted.
- For real providers, keep OAuth tokens, API keys, and message content encrypted or in a secure managed store.
- Log enough for debugging without exposing sensitive mail content in CI logs.

## Alerts

Send an immediate in-app/browser alert or optional future SMS/Telegram/email notification when:

- A recruiter asks for the user's CV or resume.
- An interview, test, or career deadline is detected.
- HR, payroll, salary, or company action is urgent.
- A home, insurance, subscription, or bill renewal is pending soon.
- A finance or account message looks security-sensitive.

## Model Strategy

Use different models or model routes by task:

- Triage model for fast classification.
- Summary model for long or complex email summaries.
- Draft model for writing reply suggestions.
- Safety model for send/delete risk checks.
- Embedding or memory model for day-by-day learning from feedback.

The model names must stay configurable so the app can switch providers or upgrade models without code rewrites.

## Learning Requirements

The agent should improve daily from:

- Category corrections.
- Approved drafts.
- Rejected drafts.
- Trash/archive decisions.
- Important sender lists.
- User notes on what is useful or useless.

This is product-level learning and preference memory. It does not require training a foundation model for the first release.

## UI And Device Requirements

- Must work on mobile, tablet, laptop, desktop, and major browsers.
- The first screen must be the actual email assistant workspace, not a marketing landing page.
- Long text must wrap cleanly and never overflow buttons, cards, panels, or mobile views.
- Important actions must be easy to approve, reject, or review.
- Bulk cleanup controls must show what is selected and protect important mail.
- The interface should be efficient for repeated daily email use.

## Engineering Requirements

- The AI-agent backend and core logic should be Python-first.
- Every feature should include tests where practical.
- CI must run syntax checks and tests.
- Keep provider integrations behind adapters.
- Keep classification and action policy separate from UI.
- Make dangerous actions reviewable and auditable.
- Use responsive layout checks before release.
- Keep requirements in source control and update them when the product changes.
