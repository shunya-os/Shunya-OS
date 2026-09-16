"""R6B-2.7 Batch C — collapse duplicate identity_id arguments.

The v2 wiring script re-appended identity_id to multi-line calls that v1 had
already patched, producing e.g.:

    ..., identity_id=TEST_ADMIN, identity_id=TEST_ADMIN,

This repairs only that duplication; it changes nothing else and adds no new
authorization decisions.
"""
from __future__ import annotations

import pathlib
import re

TESTS = pathlib.Path("/home/shunya-deploy/shunya_os/tests")
DUP = re.compile(r"identity_id=([^,\s)]+),\s*identity_id=\1")


def main():
    total = 0
    for path in sorted(TESTS.glob("test_*.py")):
        text = path.read_text()
        new, n = DUP.subn(r"identity_id=\1", text)
        if n:
            path.write_text(new)
            total += n
            print(f"  {path.name}: collapsed {n} duplicate(s)")
    print(f"total collapsed: {total}")


if __name__ == "__main__":
    main()