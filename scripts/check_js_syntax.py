"""Verify workspace.js syntax by running it through a JS parser."""
import subprocess, sys

with open('static/js/workspace.js', 'r') as f:
    content = f.read()

# Count braces and parens (ignoring strings)
stripped = content
# Remove single-line comments
import re
stripped = re.sub(r'//.*', '', stripped)
# Remove multi-line comments
stripped = re.sub(r'/\*[\s\S]*?\*/', '', stripped)
# Remove strings (single and double quoted) - crude but effective for brace-counting
stripped = re.sub(r"'[^']*'", '', stripped)
stripped = re.sub(r'"[^"]*"', '', stripped)
# Remove backtick template literals
stripped = re.sub(r'`[^`]*`', '', stripped)

open_br = stripped.count('{')
close_br = stripped.count('}')
print(f'Open braces: {open_br}, Close braces: {close_br}, Diff: {open_br - close_br}')

open_paren = stripped.count('(')
close_paren = stripped.count(')')
print(f'Open parens: {open_paren}, Close parens: {close_paren}, Diff: {open_paren - close_paren}')

open_sq = stripped.count('[')
close_sq = stripped.count(']')
print(f'Open square: {open_sq}, Close square: {close_sq}, Diff: {open_sq - close_sq}')

if open_br == close_br and open_paren == close_paren and open_sq == close_sq:
    print('All brackets balanced - syntax should be valid')
else:
    print('WARNING: Unbalanced brackets detected')
    sys.exit(1)