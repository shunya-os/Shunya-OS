from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime, timezone


@dataclass
class EmailEntity:
    id: str
    thread_id: str

    from_email: str
    to_email: List[str]

    subject: str
    date: Optional[str]
    body: str

    type: Optional[str] = None
    intent: Optional[str] = None

    destinations: List[str] = field(default_factory=list)
    dates: List[str] = field(default_factory=list)
    amounts: List[str] = field(default_factory=list)

    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )