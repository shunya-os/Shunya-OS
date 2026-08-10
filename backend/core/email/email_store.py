import json
import os

STORE_PATH = "/home/shunya-deploy/shunya_os/data/email_store.json"


def save_email(entity):
    print("DEBUG STORE PATH:", STORE_PATH)

    # Ensure directory exists
    os.makedirs(os.path.dirname(STORE_PATH), exist_ok=True)

    data = []

    # Load existing data
    if os.path.exists(STORE_PATH):
        try:
            with open(STORE_PATH, "r") as f:
                data = json.load(f)
        except Exception as e:
            print("DEBUG LOAD ERROR:", e)

    # Deduplicate by thread_id
    existing = next(
        (e for e in data if e.get("thread_id") == entity.thread_id), None
    )

    if existing:
        existing.update(entity.__dict__)
    else:
        data.append(entity.__dict__)

    # Write back
    try:
        with open(STORE_PATH, "w") as f:
            json.dump(data, f, indent=2)
        print("DEBUG WRITE SUCCESS")
    except Exception as e:
        print("DEBUG WRITE FAILED:", e)


def get_all():
    if not os.path.exists(STORE_PATH):
        return []
    with open(STORE_PATH, "r") as f:
        return json.load(f)