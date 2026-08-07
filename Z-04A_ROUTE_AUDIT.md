# Z-04A Route Integrity Audit — Verified

## Route Map (Flask + SPA)

| Route | Type | Expected Content | Verified | Notes |
|-------|------|------------------|----------|-------|
| `/` | Public | SPA Homepage — 11 elements: SHUNYA heading, Begin button, Sign In, Create Account, 4 metric cards | ✅ | SPA renders correctly |
| `/auth/` | Public | SPA Auth page — 8 elements: Sign In tab, Email, Password, Forgot password | ✅ | Sign In tab selected |
| `/auth/login` | Public | SPA Auth page — Sign In tab selected | ✅ | URL preserved, no redirect |
| `/auth/signup` | Public | SPA Auth page — Create Account tab selected, 9 elements | ✅ | **FIXED**: Previously redirected to `/auth/` |
| `/auth/forgot-password` | Public | SPA Forgot Password — 5 elements: Email, Send Reset Link | ✅ | **FIXED**: Previously showed Sign In form |
| `/auth/reset-password` | Public | SPA Reset Password — 6 elements: New password, Confirm password | ✅ | Renders correctly |
| `/auth/verify-email` | Public | SPA Verify Email — Try again, Back to sign in | ✅ | No token provided — expected behavior |
| `/auth/invitation` | Public | SPA Invitation — Back to Sign In | ✅ | No token provided — expected behavior |
| `/workspace/` | Auth | SPA Workspace shell | ✅ | Redirects to auth if no session |
| `/login` | Public | Legacy Jinja2 template — 6 elements | ✅ | Legacy — should eventually redirect to `/auth/` |
| `/logout` | Public | Logout + redirect to `/` | ⏳ | To verify |

## Routes Fixed in This Session

| Issue | Before | After |
|-------|--------|-------|
| `/auth/signup` | Redirected to `/auth/` via `replaceState` + popstate, showing Sign In | Shows Create Account tab directly |
| `/auth/login` | Redirected to `/auth/` | Shows Sign In tab directly at `/auth/login` |
| `/auth/forgot-password` | Redirected to `/auth/`, showing Sign In form | Shows Forgot Password form at `/auth/forgot-password` |
| Popstate redirect pattern | Returned null (empty render) then dispatched popstate | Unified condition renders component directly |

## Route Conflicts Identified

| Route | Handlers | Verdict |
|-------|----------|---------|
| `GET /` | `main.index` (SPA) + `shunya_bp.home` (landing.html Jinja) | `main.index` wins (registered first). Intentional — SPA overrides landing page |

## Remaining Work

- [ ] Verify `/logout` route
- [ ] Verify browser refresh on workspace
- [ ] Verify browser back/forward navigation
- [ ] Test deep links