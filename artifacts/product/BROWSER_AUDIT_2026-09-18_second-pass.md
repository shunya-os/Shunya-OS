# BROWSER AUDIT — UPDATE (second pass, production 77aa78e)

Method: real browser, authenticated session (vault login, identifier typed by me,
password never seen). All statements are measurements.

## RESOLVED: B-2 is NOT a defect — my first report was wrong

Second pass, on the Purpose step, after clicking "Skip for now — I'll add things later":

    before: sessionStorage.shunya_onboarding_step = "1"
    after : sessionStorage.shunya_onboarding_step = "2"
    view  : "Your Personal SHUNYA Is Ready" + button "Enter My SHUNYA"

The button works. The button was also measured as **not disabled** with
`pointer-events: auto`. The first pass (identical snapshot, step unchanged) was a
measurement artifact — my click evidently never reached the button. I had reported
it as a dead affordance with more confidence than the evidence supported; the
ledger correction stands and this closes it.

## CONFIRMED AND WIDER: B-4 (emoji as icons) is pervasive in the primary workspace

The authenticated Home renders its organisation navigation as:

    👤 People · 💬 Conversations ·  Work · ◇ Finance · ◆ Commercial · ○ Marketing
    ⬡ Sales · △ Operations · ◎ Knowledge · ✓ Outputs · ◈ Memory · ◈ Relationships
    ✎ Content ·  Entities · 📄 Documents

Two of the fourteen are emoji (👤 💬 ); the rest are geometric glyphs. Onboarding
adds 📋 📄 ✅ 💡  ✍️ 🔨  🔗 🌱 and the completion screen adds 👤. The design canon
explicitly prohibits emoji as icons. This is a measurable constitutional violation
across the primary workspace, not an onboarding-only issue.

## The authenticated workspace DOES render (first evidence of this)

Home renders with: the organisation orientation rail, presence ("Observing"),
the command bar ("Ask SHUNYA or type a command… ⌘K …"), "SHUNYA NOW — Live work
being performed — Nothing in motion right now", and the corrected task-based empty
text. The false-empty-state wording from the pre-campaign build is gone.

## NOT VERIFIED IN THE BROWSER: the "Ask SHUNYA" panel fix (A-2)

- Clicking the "Ask SHUNYA anything" capability card did NOT mount the resident
  panel in my session (`.sh-ai-resident` absent, no ask input, body text unchanged).
- I then verified the DEPLOYED bundle directly, to avoid a false conclusion in
  either direction: the served shell references `/assets/index-DppSV1v9.js`, and
  that 601,091-byte bundle CONTAINS my changes — markers `sh-ai-chat-empty` (2),
  `Request in progress` (1), `company data first` (1), `sh-ai-resident` (2).
  So the fix IS deployed; the click failure was not a missing fix.
- Most likely explanation: the test tab was executing a stale in-memory bundle
  loaded before the deploy, or my click did not reach the card's handler. I could
  NOT disambiguate, because this browser tool resets cookies on
  `browser_navigate`, so a fresh page load cannot hold the authenticated session
  (/workspace redirects to /auth/login) and a clean re-test is impossible here.

**Honest status: the panel fix is CI-proven (frontend tests) and its code is
confirmed present in the deployed bundle, but its human-visible behaviour is NOT
verified by me.** It must be re-tested in a browser that can hold a session across
a fresh load.

## Still open from the first pass

- **B-1** — fixed in `b0e2251` (server truth decides post-auth onboarding),
  pending deploy. Note this pass independently re-confirmed the mechanism: a fresh
  tab started at `onboarding_step = 0` on Welcome for an existing account.
- **B-3** — onboarding renders while the URL says `/auth/login` (measured again:
  `location.href` stayed `/auth/login` through steps 0→1→2).
- Public CTA 38px against a 44px minimum; zero hero images.