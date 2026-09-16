"""R6B-2.7 Batch C v2 — canonical identity for direct ObjectService calls.

v1 keyed identity off the organization argument, which breaks adversarial tests:
those deliberately pass a WRONG organization (e.g. 99999) and expect denial, so an
org-keyed map finds no identity and the call now fails closed with ValueError
instead of returning False.

Identity is a property of the test's tenancy, not of the organization argument.
v2 therefore: (a) resolves identity from the organization when it is a known
tenancy, otherwise (b) falls back to the file's canonical identity — which is the
correct behaviour for adversarial calls, because presenting your own real identity
against a victim/wrong organization must be DENIED by authorization, not by a
missing-parameter error.

Covers create/get/update/delete. Idempotent: calls already carrying identity_id
are untouched.
"""
from __future__ import annotations

import pathlib
import re

TESTS = pathlib.Path("/home/shunya-deploy/shunya_os/tests")

# file -> {"by_org": {org constant or literal: identity}, "default": identity}
MAPPING = {
    "test_g11_identity_object.py": {
        "by_org": {"ADMIN_ORG": "TEST_ADMIN", "FOUNDER_ORG": "TEST_FOUNDER"},
        "default": "TEST_ADMIN",
    },
    "test_g11_http_identity_security.py": {
        "by_org": {"1": '"g11-test-user@example.com"'},
        "default": '"g11-test-user@example.com"',
    },
}

CALL_RE = re.compile(r"\bsvc\.(create|get|update|delete)\(")
ORG_RE = re.compile(r"organization_id=([A-Za-z_][A-Za-z0-9_]*|\d+)")


def patch_file(path: pathlib.Path, spec: dict) -> int:
    by_org, default = spec["by_org"], spec["default"]
    lines = path.read_text().splitlines(keepends=True)
    out, i, patched = [], 0, 0
    while i < len(lines):
        line = lines[i]
        out.append(line)
        if CALL_RE.search(line) and "identity_id" not in line:
            org = ORG_RE.search(line)
            end = i
            if not org:
                j = i + 1
                while j < len(lines) and j < i + 12:
                    out.append(lines[j])
                    org = ORG_RE.search(lines[j])
                    end = j
                    if org or ")" in lines[j]:
                        break
                    j += 1
                i = end
            identity = by_org.get(org.group(1), default) if org else default
            if line.rstrip().endswith(")"):
                out[-1] = line.rstrip()[:-1] + f", identity_id={identity})\n"
            else:
                target = out[-1].rstrip()
                trailing = "," if target.endswith(",") else ""
                out[-1] = f"{target.rstrip(',')}, identity_id={identity}{trailing}\n"
            patched += 1
        i += 1
    path.write_text("".join(out))
    return patched


def main():
    total = 0
    for name, spec in MAPPING.items():
        p = TESTS / name
        if not p.exists():
            print(f"  SKIP (missing): {name}")
            continue
        n = patch_file(p, spec)
        total += n
        print(f"  {name}: {n} further calls given canonical identity")
    print(f"total patched: {total}")


if __name__ == "__main__":
    main()