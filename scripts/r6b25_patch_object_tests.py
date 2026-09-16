"""R6B-2.5 — give the object-convergence tests explicit canonical workspaces.

ObjectService.create() now requires an explicit workspace_id (sh_objects
.workspace_id is NOT NULL, so a workspace is part of an object's canonical
identity). These tests previously relied on the removed "spc_business" default;
each create call is updated to pass the organization's real canonical
workspace instead. Assertions are untouched.
"""
from __future__ import annotations

import pathlib
import re
import sys

PATH = pathlib.Path(
    sys.argv[1] if len(sys.argv) > 1
    else "/home/shunya-deploy/shunya_os/tests/test_g11_identity_object.py")
ORG_RE = re.compile(r"organization_id=([A-Za-z_][A-Za-z0-9_]*|\d+)")


def main():
    lines = PATH.read_text().splitlines(keepends=True)
    out = []
    i = 0
    patched = 0
    while i < len(lines):
        line = lines[i]
        out.append(line)
        if "svc.create(" in line and "workspace_id=" not in line:
            # single-line call?
            if ORG_RE.search(line) and line.rstrip().endswith(")"):
                m = ORG_RE.search(line)
                new = line.rstrip()[:-1] + \
                    f", workspace_id=_org_workspace_id({m.group(1)}))\n"
                out[-1] = new
                patched += 1
                i += 1
                continue
            # multi-line call: patch the line that carries organization_id
            j = i + 1
            while j < len(lines):
                out.append(lines[j])
                if ORG_RE.search(lines[j]):
                    m = ORG_RE.search(lines[j])
                    s = lines[j].rstrip()
                    trailing = "," if s.endswith(",") else ""
                    s = s.rstrip(",")
                    out[-1] = (
                        f"{s}, workspace_id=_org_workspace_id({m.group(1)})"
                        f"{trailing}\n"
                    )
                    patched += 1
                    j += 1
                    break
                j += 1
            i = j
            continue
        i += 1

    PATH.write_text("".join(out))
    print(f"patched {patched} svc.create calls")


if __name__ == "__main__":
    main()
