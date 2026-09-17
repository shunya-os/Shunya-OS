"""R6B-2.7 Window 6 — Block C: observable SSE liveness frame.

SSE comment heartbeats (`: ...`) keep the socket open but never reach
`EventSource.onmessage`, so the frontend cannot observe liveness. The living
presence requires a REAL data frame carrying the heartbeat, and the frontend
must not project that frame as a business reality event.
"""
import json

from app.reality_engine.sse_stream import serialize_heartbeat, serialize_heartbeat_frame


def test_comment_heartbeat_is_a_comment():
    # Retained for compatibility — still invisible to onmessage.
    assert serialize_heartbeat().startswith(": heartbeat ")


def test_heartbeat_frame_is_a_real_data_event():
    frame = serialize_heartbeat_frame()
    assert frame.startswith("data: ")
    assert frame.endswith("\n\n")

    payload = json.loads(frame[len("data: "):].strip())
    assert payload["event_type"] == "system.heartbeat"
    assert payload["event_id"].startswith("hb-")
    assert payload["timestamp"]
    assert payload["payload"]["message"] == "alive"


def test_heartbeat_frames_are_unique():
    a = serialize_heartbeat_frame()
    b = serialize_heartbeat_frame()
    assert a != b  # distinct event ids per frame
