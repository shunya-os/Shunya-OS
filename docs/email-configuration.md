# Email Configuration for Production

To enable real email delivery (identity verification, password reset, notifications),
set these environment variables:

```bash
export EMAIL_HOST=smtp.gmail.com           # SMTP server
export EMAIL_PORT=587                      # SMTP port (587 for TLS)
export EMAIL_USER=your-email@gmail.com     # SMTP username
export EMAIL_PASSWORD=your-app-password    # SMTP password or app password
export EMAIL_FROM=SHUNYA <noreply@your-domain.com>  # From address
export SHUNYA_BASE_URL=https://your-domain.com       # Base URL for links
```

For Gmail, use an App Password (requires 2FA enabled on the account):
1. Enable 2FA on your Google Account
2. Generate an App Password at https://myaccount.google.com/apppasswords
3. Use the app password as EMAIL_PASSWORD

## Development Mode

Without SMTP credentials, emails are logged to the console/application log.
The email pipeline is fully functional and verified:

- Email templates: app/email_service.py (build_verification_email, build_reset_email)
- Send core: app/communication/email_core.py (SMTP with is_human_triggered guard)
- Auth flow: app/auth_routes.py (api_signup, api_request_verification, api_verify_email, api_forgot_password)

## Verification

The email flow can be tested without SMTP:
1. POST /api/v1/auth/signup with {name, email, password}
2. Check application logs for the verification URL
3. POST /api/v1/auth/verify-email with {token: <token from log>}