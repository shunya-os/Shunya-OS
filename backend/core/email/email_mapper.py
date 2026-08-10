from backend.core.email.email_entity import EmailEntity


def map_to_email_entity(parsed: dict) -> EmailEntity:
    """Convert parsed Gmail dict into an EmailEntity.

    Normalises comma-separated To headers into a list of individual recipients.
    """
    to_raw = parsed.get("to", "")

    if isinstance(to_raw, list):
        to_list = to_raw
    elif isinstance(to_raw, str):
        # Split on comma, strip whitespace, filter empties
        to_list = [r.strip() for r in to_raw.split(",") if r.strip()]
    else:
        to_list = []

    return EmailEntity(
        id=parsed.get("id") or "",
        thread_id=parsed.get("threadId") or "",
        from_email=parsed.get("from") or "",
        to_email=to_list,
        subject=parsed.get("subject") or "",
        date=parsed.get("date"),
        body=parsed.get("body", ""),
        type=parsed.get("classification", {}).get("type"),
        intent=parsed.get("intent"),
        destinations=parsed.get("entities", {}).get("destinations", []),
        dates=parsed.get("entities", {}).get("dates", []),
        amounts=parsed.get("entities", {}).get("amounts", []),
    )