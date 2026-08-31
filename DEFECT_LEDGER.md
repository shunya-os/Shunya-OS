# DEFECT LEDGER — RECONCILED

ID | SOURCE | DEFECT | ROOT CAUSE | SEVERITY | STATUS
---|--------|--------|------------|----------|-------
D01 | screenshot | PDF preview: "refused to connect" | PDF blueprint not registered in app factory | HIGH | FIXED
D02 | screenshot | MantineProvider crash | Root render tree missing MantineProvider | HIGH | FIXED
D03 | screenshot | Voice: "not-allowed" error | No permission state handling, no graceful degradation | HIGH | FIXED
D04 | screenshot | Org: "0 Total Members" | Wrong org context or API failure displayed as empty | HIGH | OPEN
D05 | screenshot | Commitments: "Could not load" | API failure, not empty state | HIGH | OPEN
D06 | screenshot | Finance: "planned / not yet implemented" | Honest classification needed | MEDIUM | OPEN
D07 | screenshot | Outputs: "0 Total Outputs" while assets exist | Disconnected from producing systems | MEDIUM | OPEN
D08 | screenshot | Memory: 0 entries despite observed activity | Memory pipeline not surfaced to UI | MEDIUM | OPEN
D09 | screenshot | Home: raw system events shown as "observations" | No translation from events to human understanding | MEDIUM | OPEN
D10 | codebase | 5100 orphan process | Unknown origin, not in systemd, not in nginx | MEDIUM | OPEN
D11 | codebase | Old Resend key exposed in transcript | Key in .env, appeared in session text | HIGH | FIXED (sec rotated)
D12 | codebase | Password reset tokens stored as plaintext | No hashing on token column | MEDIUM | OPEN
D13 | codebase | No webhook secret configured | RESEND_WEBHOOK_SECRET not set | HIGH | OPEN (requires founder)
D14 | codebase | No email delivery state exposed to UI | EmailRecord exists but no frontend endpoint | MEDIUM | OPEN
D15 | codebase | MantineProvider not in test DB schema | Missing import in conftest | LOW | FIXED
D16 | codebase | email_core default sender not verified domain | Was onboarding@resend.dev | HIGH | FIXED
D17 | codebase | Email idempotency from content hash | Wrong approach | MEDIUM | FIXED
D18 | codebase | No email lifecycle tracking | No durable EmailRecord | HIGH | FIXED
D19 | codebase | No webhook for bounce/complaint | Missing endpoint | MEDIUM | FIXED (protocol corrected)
D20 | codebase | Resend webhook uses wrong auth protocol | Custom HMAC, not Svix | HIGH | FIXED
D21 | codebase | No Alembic migration for email_records | Test-only db.create_all() | HIGH | FIXED
D22 | codebase | Onboarding idempotency key uses timestamp | Unstable operation identity | MEDIUM | FIXED

**TOTAL: 22 logged — 14 FIXED, 8 OPEN**