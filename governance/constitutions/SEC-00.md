# SEC-00 — Security Preservation Constitution

**Status:** PERMANENT
**Adopted:** 2026-08-06

---

## Principle

Every infrastructure repair, deployment, migration, or production change
shall preserve or improve the existing enterprise-grade security posture.

Under no circumstance may a repair reduce security in order to restore
functionality.

## Protection Checklist

During every recovery, the following shall be verified and preserved:

- TLS 1.2/1.3 with strong cipher suites
- HSTS
- Secure HTTP headers (CSP, X-Frame-Options, X-Content-Type-Options,
  Referrer-Policy, Permissions-Policy)
- Secure cookies (HttpOnly, Secure, SameSite)
- CSRF protection
- XSS protection
- SQL injection protection
- Rate limiting
- Authentication and authorization
- RBAC / permissions
- Secret management
- Environment variable isolation
- Database security
- File upload validation
- Audit logging
- Encryption at rest (where configured)
- Encryption in transit
- Session management
- API security
- CORS policy
- Reverse proxy hardening
- Firewall configuration
- SSH hardening
- Automatic security updates (where appropriate)
- Fail2Ban or equivalent intrusion protection (if already configured)
- Backup integrity
- Disaster recovery capability

## Requirements

If any existing protection from the legacy deployment is missing in the new
deployment, it shall be restored before declaring production readiness.

No convenience workaround is permitted if it weakens security.

Every production change shall conclude with a Security Regression Check
confirming that the security posture is unchanged or improved.

Security is constitutional and shall not be traded for speed.

---

## Canonical Reference

See `CONSTITUTION.md` at the repository root for the full constitutional framework.