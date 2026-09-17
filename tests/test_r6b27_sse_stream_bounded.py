"""R6B-2.7 Window 5 — SSE stream must not outlive the gunicorn worker timeout.

Production defect: gunicorn ran with the DEFAULT SYNC worker class and
``--timeout 60``. An SSE response blocks one whole sync worker for the entire
life of the connection, so a handful of concurrent clients starved the site and
the arbiter SIGKILLed the offending workers — 111 such kills in two hours,
reported as "Perhaps out of memory?" even though memory was free.

The stream now ends itself cleanly well before the worker timeout, and asks the
browser to reconnect (EventSource does so automatically), so the client
experience is unchanged while the worker is released.
"""
import pytest


class TestStreamIsBounded:
    def _config(self, app):
        # Keep the test fast while proving the same code path.
        app.config["SSE_MAX_STREAM_SECONDS"] = 1.0
        app.config["SSE_DRAIN_TIMEOUT"] = 0.2

    def _login(self, client):
        with client.session_transaction() as sess:
            sess["identity_id"] = "sid_sse_test"
            sess["user_id"] = 1
            sess["current_org_id"] = 1
            sess["tenant_id"] = 1

    def test_stream_terminates_and_is_not_unbounded(self, app, client):
        self._config(app)
        self._login(client)

        resp = client.get("/api/v1/reality/stream")

        assert resp.status_code == 200
        assert resp.mimetype == "text/event-stream"
        # Reading the body forces the generator to run to completion. If the
        # stream were unbounded this call would never return.
        body = resp.get_data(as_text=True)
        # A reconnect hint is advertised so the client comes straight back.
        assert "retry:" in body
        assert "X-Accel-Buffering" in resp.headers

    def test_stream_requires_authentication(self, app, client):
        self._config(app)
        resp = client.get("/api/v1/reality/stream")
        assert resp.status_code == 401

    def test_client_is_unregistered_after_the_stream_ends(self, app, client):
        """The per-client queue must not leak when the stream closes."""
        self._config(app)
        self._login(client)

        from app.reality_engine.sse_stream import get_sse_manager
        manager = get_sse_manager()
        before = len(getattr(manager, "_clients", {}))

        resp = client.get("/api/v1/reality/stream")
        resp.get_data(as_text=True)

        after = len(getattr(manager, "_clients", {}))
        assert after <= before
