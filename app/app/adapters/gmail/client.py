"""
SHUNYA — Gmail Provider Client Interface (Phase 3)
Injectable client interface with fakes for tests.
"""
from datetime import datetime
from typing import Optional
from googleapiclient.discovery import build


class GmailClientInterface:
    """Injectable Gmail API client interface.
    Real implementation uses google-api-python-client."""

    def list_messages(self, query: str = "", max_results: int = 50,
                      page_token: str = "") -> dict:
        """List messages matching query. Returns dict with messages[], nextPageToken."""
        raise NotImplementedError

    def get_message(self, message_id: str) -> dict:
        """Get a single message by ID."""
        raise NotImplementedError

    def get_thread(self, thread_id: str) -> dict:
        """Get a full thread by ID."""
        raise NotImplementedError

    def list_history(self, start_history_id: str,
                     history_types: list = None) -> dict:
        """List history changes since start_history_id."""
        raise NotImplementedError

    def watch(self, topic_name: str, label_ids: list = None) -> dict:
        """Set up Gmail watch for push notifications."""
        raise NotImplementedError

    def stop_watch(self) -> dict:
        """Stop watching for changes."""
        raise NotImplementedError

    def get_profile(self) -> dict:
        """Get Gmail profile (email address, historyId)."""
        raise NotImplementedError


class RealGmailClient(GmailClientInterface):
    """Real Gmail API client using google-api-python-client.
    Injected via credential_reference resolution. No live calls in automated tests."""

    def __init__(self, credentials=None, token: str = ""):
        self._service = None
        if credentials:
            self._service = build("gmail", "v1", credentials=credentials)
        elif token:
            from google.oauth2.credentials import Credentials
            creds = Credentials(token=token)
            self._service = build("gmail", "v1", credentials=creds)

    def list_messages(self, query: str = "", max_results: int = 50,
                      page_token: str = "") -> dict:
        if not self._service:
            return {"messages": [], "resultSizeEstimate": 0}
        kwargs = {"userId": "me", "maxResults": max_results, "q": query}
        if page_token:
            kwargs["pageToken"] = page_token
        result = self._service.users().messages().list(**kwargs).execute()
        return result

    def get_message(self, message_id: str) -> dict:
        if not self._service:
            return {}
        return self._service.users().messages().get(userId="me", id=message_id, format="full").execute()

    def get_thread(self, thread_id: str) -> dict:
        if not self._service:
            return {"id": thread_id, "messages": []}
        return self._service.users().threads().get(userId="me", id=thread_id).execute()

    def list_history(self, start_history_id: str,
                     history_types: list = None) -> dict:
        if not self._service:
            return {"history": [], "historyId": start_history_id}
        kwargs = {"userId": "me", "startHistoryId": start_history_id}
        if history_types:
            kwargs["historyTypes"] = history_types
        return self._service.users().history().list(**kwargs).execute()

    def watch(self, topic_name: str, label_ids: list = None) -> dict:
        if not self._service:
            return {"historyId": "0", "expiration": "0"}
        body = {"topicName": topic_name, "labelIds": label_ids or []}
        return self._service.users().watch(userId="me", body=body).execute()

    def stop_watch(self) -> dict:
        if not self._service:
            return {}
        return self._service.users().stop(userId="me").execute()

    def get_profile(self) -> dict:
        if not self._service:
            return {"emailAddress": "", "historyId": "0"}
        return self._service.users().getProfile(userId="me").execute()


class FakeGmailClient(GmailClientInterface):
    """Fake Gmail client for testing.
    Returns deterministic data without real API calls."""

    def __init__(self):
        self._messages = {}
        self._threads = {}
        self._history_id = "1000"
        self._history = []

    def add_message(self, msg_id: str, thread_id: str, from_addr: str,
                    subject: str = "", body: str = "",
                    internal_date: int = 1700000000000):
        self._messages[msg_id] = {
            "id": msg_id, "threadId": thread_id,
            "internalDate": str(internal_date),
            "payload": {
                "headers": [
                    {"name": "From", "value": from_addr},
                    {"name": "Subject", "value": subject},
                ],
                "parts": [{"mimeType": "text/plain",
                           "body": {"data": body.encode("utf-8").hex()}}],
            },
        }
        if thread_id not in self._threads:
            self._threads[thread_id] = {"id": thread_id, "messages": []}
        self._threads[thread_id]["messages"].append(self._messages[msg_id])

    def add_history(self, history_id: str, message_ids: list):
        self._history.append({
            "id": history_id,
            "messagesAdded": [{"message": self._messages[msg_id]}
                              for msg_id in message_ids if msg_id in self._messages],
        })

    def list_messages(self, query: str = "", max_results: int = 50,
                      page_token: str = "") -> dict:
        result = list(self._messages.values())[:max_results]
        return {"messages": result, "resultSizeEstimate": len(result)}

    def get_message(self, message_id: str) -> dict:
        return self._messages.get(message_id, {})

    def get_thread(self, thread_id: str) -> dict:
        return self._threads.get(thread_id, {"id": thread_id, "messages": []})

    def list_history(self, start_history_id: str,
                     history_types: list = None) -> dict:
        return {"history": self._history, "historyId": self._history_id}

    def watch(self, topic_name: str, label_ids: list = None) -> dict:
        return {"historyId": self._history_id, "expiration": "1800000"}

    def stop_watch(self) -> dict:
        return {}

    def get_profile(self) -> dict:
        return {"emailAddress": "test@gmail.com", "historyId": self._history_id}