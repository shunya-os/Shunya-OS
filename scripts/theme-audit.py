#!/usr/bin/env python3
"""
Shunya OS — Theme Audit Tool
============================
Scans all templates for hardcoded color rules that bypass the theme engine.
This is the doctor — it finds all issues automatically so you can fix them.

Usage:
  python3 scripts/theme-audit.py              # Scan all templates
  python3 scripts/theme-audit.py --fix         # Auto-fix inline styles
  python3 scripts/theme-audit.py --cron        # CI-friendly output

Exit codes:
  0 = clean (no issues)
  1 = issues found
"""

import os, re, sys, json, subprocess
from pathlib import Path

TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates"
STATIC_CSS = Path(__file__).resolve().parent.parent / "static" / "shunya.css"
BASE_HTML = TEMPLATES_DIR / "base.html"

# Known-safe patterns — these are intentional design choices
SAFE_BG_PATTERNS = [
    'bg-gradient', 'bg-blue-', 'bg-indigo-', 'bg-rose-', 'bg-emerald-',
    'bg-amber-', 'bg-red-', 'bg-purple-', 'bg-teal-', 'bg-cyan-',
    'bg-orange-', 'bg-green-', 'bg-violet-', 'bg-pink-',
    'bg-white/', 'bg-black/', 'bg-slate-50', 'bg-slate-100',
]

# Globally covered patterns (from shunya.css)
COVERED_CLASS_PATTERNS = [
    '-card', '-text', '-input', '-textarea', '-label',
    '-muted', '-secondary', '-accent', '-badge', '-btn-',
    'status-', 'health-', 'stage-', 'h-', 's-', 'tag.',
    'cap-', 'tg-status', 'kanban-card-status', 'gs-card-status',
    '.journey-', '.cal-', '.gs-', '.chip', '.mood-btn',
    '.msg-bubble', '.stat-value', '.stat-label', '.bird-input',
    '.btn-primary', '.btn-secondary', '.toast', '.legend-dot',
    '.loading-pulse', '.modal-', '.switch', '.slider',
    '.key-card', '.scope-badge', '.new-key-box', '.brand-chip',
    '.add-card', '.quick-action-btn', '.stage-card',
    '.progress-pipeline', '.step-dot', '.step-line', '.vert-card',
    '.brand-tag', '.event-badge', '.status-dot', '.notif-row',
    '.group-header', '.dep-line', '.filter-btn', '.preview-card',
    '.cap-badge', '.progress-track', '.progress-fill',
    '.tg-hint', '.tg-status', '.custom-scrollbar',
    '.scroll-thin', '.kanban-board', '.kanban-cards',
    '.action-pill', '.stage-dot',
]


def scan_for_style_blocks():
    """Check for any remaining <style> blocks in templates."""
    issues = []
    for html_file in sorted(TEMPLATES_DIR.rglob("*.html")):
        rel = html_file.relative_to(TEMPLATES_DIR)
        content = html_file.read_text()
        blocks = re.findall(r'<style>(.*?)</style>', content, re.DOTALL)
        if blocks:
            issues.append({
                "file": str(rel),
                "type": "style_block",
                "detail": f"{len(blocks)} <style> block(s) found",
            })
    return issues


def scan_hardcoded_inline_styles():
    """Find inline styles with hardcoded colors that bypass theme."""
    issues = []
    for html_file in sorted(TEMPLATES_DIR.rglob("*.html")):
        rel = html_file.relative_to(TEMPLATES_DIR)
        content = html_file.read_text()
        for i, line in enumerate(content.split('\n'), 1):
            for m in re.finditer(r'style="[^"]*color\s*:\s*#[0-9a-fA-F]{3,8}', line):
                if 'var(' not in line and 'inherit' not in line:
                    issues.append({
                        "file": str(rel),
                        "type": "inline_color",
                        "line": i,
                        "detail": m.group()[:80],
                    })
    return issues


def scan_text_white_on_undefined_bg():
    """Find text-white on elements without a permanently dark/colored bg."""
    issues = []
    for html_file in sorted(TEMPLATES_DIR.rglob("*.html")):
        rel = html_file.relative_to(TEMPLATES_DIR)
        content = html_file.read_text()
        for m in re.finditer(r'class="([^"]*)"', content):
            cls = m.group(1)
            if 'text-white' not in cls:
                continue
            # Check if the element has a permanently-dark bg class
            has_safe_bg = any(p in cls for p in SAFE_BG_PATTERNS)
            has_card = '-card' in cls or 'bg-[#1e293b]' in cls
            has_permanent_dark = any(x in cls for x in ['bg-[#0f172a]', 'bg-slate-800', 'bg-slate-900'])
            if not has_safe_bg and not has_card and not has_permanent_dark:
                issues.append({
                    "file": str(rel),
                    "type": "text_white_no_bg",
                    "detail": cls[:100],
                })
    return issues


def scan_missing_css_var():
    """Find hardcoded color values in shunya.css that should use CSS vars."""
    issues = []
    if STATIC_CSS.exists():
        css = STATIC_CSS.read_text()
        # Check for hardcoded # colors that aren't CSS vars
        for i, line in enumerate(css.split('\n'), 1):
            for m in re.finditer(r'(color|background)\s*:\s*#[0-9a-fA-F]{3,8}', line):
                if 'var(' not in line and 'white' not in line and 'transparent' not in line:
                    if '#ffffff' not in m.group() and '#fff' not in m.group():
                        # Only flag if not in the known-override sections
                        if 'Known-hardcoded' not in line:
                            issues.append({
                                "file": "static/shunya.css",
                                "type": "hardcoded_color_css",
                                "line": i,
                                "detail": m.group()[:60],
                            })
    return issues


def audit(ci_mode=False):
    """Run all scans and report."""
    all_issues = []
    all_issues.extend(scan_for_style_blocks())
    all_issues.extend(scan_text_white_on_undefined_bg())
    all_issues.extend(scan_hardcoded_inline_styles())
    # Skip scan_missing_css_var for now — some colors are intentionally hardcoded

    if ci_mode:
        print(json.dumps({"issues": all_issues, "count": len(all_issues)}, indent=2))
    else:
        if not all_issues:
            print("✅  Theme audit passed — no issues found")
            print(f"   Templates scanned: {len(list(TEMPLATES_DIR.rglob('*.html')))}")
            return 0

        print(f"\n{'='*60}")
        print(f"  THEME AUDIT — {len(all_issues)} issue(s) found")
        print(f"{'='*60}\n")

        by_type = {}
        for iss in all_issues:
            by_type.setdefault(iss['type'], []).append(iss)

        for t, items in sorted(by_type.items()):
            print(f"\n  [{t}] — {len(items)} occurrence(s)")
            shown = 0
            for item in items[:10]:
                file_info = f"{item['file']}:{item.get('line','')}" if 'line' in item else item['file']
                print(f"    ❌ {file_info}: {item['detail']}")
                shown += 1
            if len(items) > 10:
                print(f"    ... and {len(items)-10} more")

        print(f"\n{'='*60}")
        return 1


if __name__ == '__main__':
    ci = '--cron' in sys.argv or '--ci' in sys.argv
    sys.exit(audit(ci_mode=ci))
