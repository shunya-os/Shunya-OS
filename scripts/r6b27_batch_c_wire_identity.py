"""R6B-2.7 Batch C — wire canonical identity into direct ObjectService test calls.

The fail-closed contract requires an identity on every canonical create/get/update.
Tests that exercise authorization must therefore supply the REAL canonical identity
for the organization they operate in — not a synthetic one — so that the
authorization path is genuinely exercised rather than bypassed.

This script adds ``identity_id=<identity constant>`` to direct ``svc.create`` /
``svc.get`` / ``svc.update`` calls in the test files, using an explicit,
per-file mapping from the organization constant to the canonical identity
constant that the file's own fixture provisions membership for.

Explicit mapping only. No inference, no string similarity, no defaults.
Idempotent: calls that already carry identity_id are left untouched.
"""
from __future__ import annotations

import pathlib
import re

TESTS = pathlib.Path("/home/shunya-deploy/shunya_os/tests")

# file -> {organization constant used in the call: canonical identity constant}
MAPPING = {
    "test_g11_identity_object.py": {
        "ADMIN_ORG": "TEST_ADMIN",
        "FOUNDER_ORG": "TEST_FOUNDER",
    },
    "test_g11_http_identity_security.py": {
        "1": '"g11-test-user@example.com"',
    },
}

# only these ObjectService methods take identity authorization
CALL_RE = re.compile(r"\bsvc\.(create|get|update)\(")
ORG_RE = re.compile(r"organization_id=([A-Za-z_][A-Za-z0-9_]*|\d+)")


def patch_file(path: pathlib.Path, mapping: dict) -> int:
    lines = path.read_text().splitlines(keepends=True)
    out, i, patched = [], 0, 0
    while i < len(lines):
        line = lines[i]
        out.append(line)
        m = CALL_RE.search(line)
        if m and "identity_id" not in line:
            # find the organization_id within this call (same line or the block)
            block_end = i
            org = ORG_RE.search(line)
            if not org:
                j = i + 1
                while j < len(lines) and j < i + 12:
                    out.append(lines[j])
                    org = ORG_RE.search(lines[j])
                    if org:
                        block_end = j
                        break
                    if ")" in lines[j]:
                        block_end = j
                        break
                    j += 1
                i = block_end
            if org and org.group(1) in mapping:
                identity = mapping[org.group(1)]
                # single-line call?
                if line.rstrip().endswith(")"):
                    out[-1] = line.rstrip()[:-1] + f", identity_id={identity})\n"
                    patched += 1
                else:
                    target = out[-1].rstrip()
                    trailing = "," if target.endswith(",") else ""
                    target = target.rstrip(",")
                    out[-1] = f"{target}, identity_id={identity}{trailing}\n"
                    patched += 1
        i += 1
    path.write_text("".join(out))
    return patched


def main():
    total = 0
    for name, mapping in MAPPING.items():
        p = TESTS / name
        if not p.exists():
            print(f"  SKIP (missing): {name}")
            continue
        n = patch_file(p, mapping)
        total += n
        print(f"  {name}: {n} calls given canonical identity")
    print(f"total patched: {total}")


if __name__ == "__main__":
    main()
