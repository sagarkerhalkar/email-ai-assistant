def get_sample_emails():
    return [
        {
            "id": "mail-001",
            "from": "offers@bajaj-finance.example",
            "senderName": "Bajaj Finance",
            "subject": "Pre-approved personal loan offer with instant approval",
            "receivedAt": "2026-06-26T09:15:00+05:30",
            "body": (
                "Congratulations. You are eligible for a pre-approved personal loan with instant disbursal, "
                "special EMI options, and limited period processing fee benefits. Click now to apply. "
                "This promotional message is sent to selected customers. Unsubscribe if you do not want these offers."
            ),
        },
        {
            "id": "mail-002",
            "from": "rhea.kapoor@talentbridge.example",
            "senderName": "Rhea Kapoor",
            "subject": "Backend Engineer role - please share your CV",
            "receivedAt": "2026-06-26T10:05:00+05:30",
            "body": (
                "Hi, I found your profile suitable for a Backend Engineer role. Could you please share your "
                "latest CV or resume today? If you are interested, I can schedule an interview discussion for Monday. Regards, Rhea."
            ),
        },
        {
            "id": "mail-003",
            "from": "payroll@company.example",
            "senderName": "Company Payroll",
            "subject": "June salary slip and payroll confirmation",
            "receivedAt": "2026-06-26T08:30:00+05:30",
            "body": (
                "Dear employee, your June salary slip has been generated. Please review the attached payslip "
                "and confirm if there is any discrepancy in basic pay, deductions, reimbursement, or tax declaration by 30 June."
            ),
        },
        {
            "id": "mail-004",
            "from": "learn@engineering-notes.example",
            "senderName": "Engineering Notes",
            "subject": "Study note: practical guide to event-driven systems",
            "receivedAt": "2026-06-25T21:10:00+05:30",
            "body": (
                "This week's study mail covers event-driven systems in depth. Event-driven architecture helps services "
                "communicate through messages and durable queues instead of direct synchronous calls. It improves resilience "
                "when downstream systems are slow, but it introduces complexity around ordering, retries, idempotency, "
                "observability, and schema evolution. A practical implementation starts with a clear domain event model, "
                "a dead-letter queue, retry budgets, consumer idempotency keys, and trace identifiers. Teams should also "
                "document ownership of every event and create dashboards for lag, error rate, and replay safety. The key "
                "lesson is to start with one workflow where asynchronous delivery solves a real business problem, then expand "
                "after testing failure modes."
            ),
        },
        {
            "id": "mail-005",
            "from": "renewals@homeconnect.example",
            "senderName": "HomeConnect",
            "subject": "Internet plan renewal due tomorrow",
            "receivedAt": "2026-06-26T07:50:00+05:30",
            "body": (
                "Your home internet plan renewal is due tomorrow. Please renew before 27 June to avoid service interruption. "
                "The current plan includes fiber broadband and router support."
            ),
        },
        {
            "id": "mail-006",
            "from": "notifications@social.example",
            "senderName": "Social App",
            "subject": "You have new profile views",
            "receivedAt": "2026-06-25T18:45:00+05:30",
            "body": (
                "You have 12 new profile views and 4 new reactions this week. Open the app to see who interacted with your updates."
            ),
        },
        {
            "id": "mail-007",
            "from": "deals@shopping.example",
            "senderName": "Shopping Deals",
            "subject": "Weekend sale and extra discount coupon",
            "receivedAt": "2026-06-25T12:45:00+05:30",
            "body": (
                "Weekend sale is live with extra discount coupons and limited period deals. Unsubscribe if you do not want promotions."
            ),
        },
    ]
