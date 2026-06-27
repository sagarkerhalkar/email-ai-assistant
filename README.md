# Email AI Assistant

This repo contains a Python-first foundation for an AI email agent. It triages mail, summarizes long messages, prepares reply drafts, flags recruiter/CV requests, bulk-selects unnecessary mail for one-shot cleanup, and stores learning feedback over time.

## Run Locally

Install Python 3.11 or newer, then run:

```powershell
python app.py
```

Then open:

```text
http://localhost:4173
```

## Test

```powershell
python -m unittest discover -s tests
```

The project uses only the Python standard library for now, so no package install is required.

## Mailbox Account

Set your local mailbox address in `.env`:

```text
MAILBOX_EMAIL=your.gmail.address@gmail.com
GMAIL_ENABLED=true
GMAIL_CREDENTIALS_PATH=private/gmail_credentials.json
GMAIL_TOKEN_PATH=private/gmail_token.json
GMAIL_REDIRECT_URI=http://localhost:4173/
CV_FILE_PATH=private/cv.pdf
DRAFT_ATTACHMENTS_DIR=private/attachments
```

The app shows that account and uses safe sample data until Gmail OAuth is connected.

## Connect Gmail

1. Put the downloaded Google OAuth client file at `private/gmail_credentials.json`.
2. Run the app and open `http://localhost:4173`.
3. Click `Connect Gmail`.
4. Sign in with your Gmail account.
5. Allow Gmail access.
6. Return to the app and refresh.

After connection, Gmail tokens are stored locally at `private/gmail_token.json`. The `private/` folder is ignored by Git.

## CV And Attachments

Put your latest CV here:

```text
private/cv.pdf
```

Put other approved attachments here:

```text
private/attachments/
```

When an email asks for a CV, resume, portfolio, certificate, document, ID proof, or payslip, the draft screen shows suggested attachments. The app sends attachments only when you approve the draft.

If your CV is currently inside Gmail, connect Gmail first, then click `Find CV files`. The app searches Gmail attachments and saves matching files into `private/attachments/`.

## What Is Implemented

- Source-of-truth product requirements in `docs/PRODUCT_REQUIREMENTS.md` and `src/email_ai_assistant/requirements.py`.
- Python agent pipeline in `src/email_ai_assistant/agent.py`.
- Category rules for finance, HR/company, career/recruiters, home renewals, study/long-form, social, marketing, and low-value loan offers.
- Summary generation for long emails.
- Draft generation for emails that need a reply.
- Human approval gate before sending.
- Bulk select and one-shot Trash cleanup for cleanable low-value messages.
- Protection rules so salary, bank, HR, recruiter, home renewal, and personal mail cannot be bulk-deleted.
- In-app/browser alerts, so WhatsApp Business is not required.
- Daily learning storage through feedback in `data/agent-memory.json`.
- Responsive browser UI for desktop, laptop, tablet, and mobile.
- CI workflow in `.github/workflows/ci.yml`.

## Integration Roadmap

Real mailbox and notification actions are adapter-based:

- `src/email_ai_assistant/integrations/mail_provider.py` will be extended with Gmail or Microsoft OAuth.
- `src/email_ai_assistant/integrations/notification_provider.py` can later add Telegram, SMS, email, or WhatsApp if you decide to use it.
- `src/email_ai_assistant/model_router.py` maps each task to a separate configurable model.

The current version uses safe sample data and mock send/Trash behavior so the workflow can be tested without risking real email deletion or sending.
