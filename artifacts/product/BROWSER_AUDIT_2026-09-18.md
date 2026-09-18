# BROWSER AUDIT — production shunyaos.com (measured, not judged)

Date: 2026-09-18 · deployed SHA at time of audit: a7457d0 (verified via /health build_id)
Method: real browser session against production. No vision capability exists in this
session, so every statement below is a MEASUREMENT (DOM, computed style, storage,
layout) — none of it is a visual/taste judgement. Visual quality (§30) therefore
remains the founder's call; these are the facts to judge from.

## Public landing (/) — measured at 1280x577, dpr 1

- Renders: शून्य (h1, 48px), SHUNYA (h2), tagline "INFINITE INTELLIGENCE. ZERO NOISE.
  An intelligent operating system that understands your business as a living system,
  not a database.", one primary CTA "Get Started".
- Fonts actually loaded: Inter, Playfair Display, Noto Sans Devanagari — matches the
  canonical typography set.
- Contrast: tagline 5.68:1 (passes AA 4.5), h1 16.17:1, CTA white-on-#1A1C1D 17.1:1.
  (An earlier reading of 1.06:1 was MY measurement error — it compared the button's
  text against the page background instead of the button's own background. Corrected.)
- Page background rgb(251,248,245) — warm off-white, light-first.
- No horizontal overflow. 50 elements, 21 visible, 199 characters of text.
- **No images at all** (`document.querySelectorAll('img')` is empty) — the hero
  artwork is the declared `TODO: Import actual SVG hero artwork…` in
  `frontend/src/components/public/homepage.tsx`. §28 placeholder surface.

## Login (/auth/login) — renders correctly

- EMAIL + PASSWORD textboxes (accessible names present), disabled-until-valid
  "Sign In", "Forgot password?", "Create account", "Sign in with Google",
  "Sign in with GitHub".
- Sign-in SUCCEEDED in the real browser with the saved credential. No JS errors,
  no console messages during the whole flow.

## DEFECT B-1 — an existing account is forced through FIRST-TIME onboarding

- After a successful sign-in the SPA rendered "Welcome to Your Personal SHUNYA"
  onboarding, not the workspace, for an account that already exists.
- Cause (measured): the session lives in **sessionStorage** (`shunya_session` =
  `{"identityId":"sid_…","email":"…"}`) and the onboarding step in
  **sessionStorage** (`shunya_onboarding_step=1`). There is NO completion flag in
  localStorage or sessionStorage (`shunya_onboarding_complete` is absent), so
  `isOnboardingComplete()` is false on every new tab and onboarding replays.
- Consequences: (a) an existing user is treated as brand new on any new tab or
  device; (b) the identity/organization gate is skippable, so the product can be
  entered without establishing context.
- Directive references: M5 ("no dead-end screens", entry→workspace), §32 continuity
  (ACTION → CLOSE TAB → REOPEN must return to truthful state).

## DEFECT B-2 — "Skip for now — I'll add things later" does nothing

- Clicked it; the rendered snapshot was byte-identical afterwards and the persisted
  `shunya_onboarding_step` stayed at `1`. Two independent measurements agree.
- §28: "No dead visual affordances. No buttons that do nothing." This is on the
  primary onboarding surface, and it is the escape hatch a stuck user would take.

## DEFECT B-3 — onboarding renders while the URL says /auth/login

- `location.href` remained `https://shunyaos.com/auth/login` throughout the
  onboarding screens. State and URL disagree, so a refresh or a bookmark lands on
  the login page rather than where the human actually is.

## DEFECT B-4 — emoji used as icons

- Onboarding steps use 📋 📄 ✅ 💡 (welcome) and 📤 ✍️ 🔨 🏢 🔗 🌱 (purpose).
- The design canon explicitly prohibits emoji as icons ("Prohibited iconography:
  emoji as icons, filled glyphs, multi-colour/gradient icons"). This is a
  measurable constitutional violation, not a matter of taste.

## Measured but NOT yet judged

- The authenticated Home, the workspace shell, the AI resident panel and the
  "Ask SHUNYA" affordance were not reached in this pass: the panel fix
  (`expanded` default) is in `84af32d`, which had not deployed at the time of this
  audit. Testing that surface before deploy would only re-measure the old build.
- Touch target: the public CTA measures 116x38px. The mobile canon and WCAG 2.5.5
  require >= 44px; 38px is under. Recorded as a measurement, to be confirmed across
  the other primary controls.
