#!/usr/bin/env python3

import os
import sys

os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

from google_auth_oauthlib.flow import InstalledAppFlow

# === CONFIG ===
SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/contacts.readonly",
    "https://www.googleapis.com/auth/calendar",
]

CREDENTIALS_FILE = "credentials/credentials.json"
TOKEN_FILE = "credentials/token.json"


def main():
    # Check credentials file
    if not os.path.exists(CREDENTIALS_FILE):
        print(f"\n❌ Missing: {CREDENTIALS_FILE}")
        sys.exit(1)

    flow = InstalledAppFlow.from_client_secrets_file(
        CREDENTIALS_FILE,
        SCOPES
    )

    print("\n=== STEP 1 ===")
    print("Open this URL in your browser:\n")

    flow.redirect_uri = "http://localhost:8080/"

    auth_url, _ = flow.authorization_url(
      prompt='consent',
      access_type='offline'
    )

    print(auth_url)

    print("\n=== STEP 2 ===")
    print("After login, you will be redirected to a URL.")
    print("Copy FULL URL and paste below.\n")

    redirect_response = input("PASTE FULL REDIRECT URL HERE:\n")

    flow.fetch_token(authorization_response=redirect_response)

    creds = flow.credentials

    os.makedirs("credentials", exist_ok=True)

    with open(TOKEN_FILE, "w") as f:
        f.write(creds.to_json())

    print("\n✅ TOKEN SAVED SUCCESSFULLY")
    print(f"Saved at: {TOKEN_FILE}")


if __name__ == "__main__":
    main()
