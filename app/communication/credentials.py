"""
SHUNYA — Credential Resolver (Phase 3)
Narrow secret-resolution boundary.
CommunicationSource stores credential_reference only.
Adapters request credentials through this resolver.
"""
import os


class CredentialResolver:
    """Resolves credential references to actual secrets.
    Credential references are keys/names, never secrets themselves."""

    @staticmethod
    def resolve(ref: str) -> str:
        """
        Resolve a credential reference to a secret value.
        Supported formats:
          env:VAR_NAME     → os.environ[VAR_NAME]
          file:/path       → read file contents
          literal:value    → direct value (for tests only)
        """
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
            return ref[8:]

        return ""

    @staticmethod
    def is_secret_field(field_name: str) -> bool:
        """Check if a field name suggests secret content."""
        secret_keywords = ["token", "secret", "password", "key", "credential",
                          "refresh", "access_token", "auth", "session"]
        return any(kw in field_name.lower() for kw in secret_keywords)