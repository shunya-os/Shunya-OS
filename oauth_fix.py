from google_auth_oauthlib.flow import InstalledAppFlow

flow = InstalledAppFlow.from_client_secrets_file(
    "credentials/credentials.json",
    scopes=[
        "https://www.googleapis.com/auth/gmail.readonly",
        "https://www.googleapis.com/auth/contacts.readonly",
        "https://www.googleapis.com/auth/calendar"
    ]
)

flow.redirect_uri = "urn:ietf:wg:oauth:2.0:oob"

auth_url, _ = flow.authorization_url(prompt='consent')

print("\nOPEN THIS URL:\n")
print(auth_url)

code = "4/1AXEQxIAAH4dVkkRPQC2HWyfSv366645seiCpNNKrR2jGHzk6ZPa8rbhHzu4"

flow.fetch_token(code=code)

creds = flow.credentials

with open("credentials/token.json", "w") as f:
    f.write(creds.to_json())

print("\n✅ TOKEN SAVED SUCCESSFULLY\n")
