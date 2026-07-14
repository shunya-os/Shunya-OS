"""
SHUNYA — Credential Resolver (Phase 3)
Narrow secret-resolution boundary.
CommunicationSource stores credential_reference only.
Adapters request credentials through this resolver.
"""
import os

IN_TESTING = os.getenv("TESTING", "").lower() in ("true", "1", "yes")


class CredentialResolver:
    """Resolves credential references to actual secrets.
    Credential references are keys/names, never secrets themselves.

    Production-safe mechanisms:
      env:REFERENCE_NAME   -> os.environ[REFERENCE_NAME]
      file:PATH            -> read file contents

    TESTING-only mechanism:
      literal:value        -> direct value (rejected outside TESTING)
    """

    @staticmethod
    def resolve(ref: str) -> str:
        if not ref:
            return ""

        if ref.startswith("env:"):
            var_name = ref[4:]
            return os.getenv(var_name, "")

        if ref.startswith("file:"):
            path = ref[5:]
            try:
                with open(path) as f:
                    return f.read().strip()
            except (FileNotFoundError, PermissionError, OSError):
                return ""

        if ref.startswith("literal:"):
            if not IN_TESTING:
                return ""  # rejected outside TESTING
            return ref[8:]

        return ""

    @staticmethod
    def is_secret_field(field_name: str) -> bool:
        secret_keywords = ["token", "secret", "password", "key", "credential",
                          "refresh", "access_token", "auth", "session"]
        return any(kw in field_name.lower() for kw in secret_keywords)