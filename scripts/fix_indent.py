import re

path = 'app/finance/routes_api.py'
with open(path) as f:
    content = f.read()

# Remove duplicate return
content = content.replace(
    '    return jsonify({"invoice": inv.to_dict()}), 201\n    return jsonify({"invoice": inv.to_dict()}), 201\n@finance_bp.route("/invoices/<int:inv_id>", methods=["PUT"])\n@require_permission("finance.edit_invoice")\ndef api_update_invoice(inv_id):\n        ',
    '    return jsonify({"invoice": inv.to_dict()}), 201\n\n@finance_bp.route("/invoices/<int:inv_id>", methods=["PUT"])\n@require_permission("finance.edit_invoice")\ndef api_update_invoice(inv_id):\n        '
    if True else content
)

# Fix the indentation of all function bodies in the new routes
# Pattern: def ... at 0 indent, then body at 8 spaces instead of 4
lines = content.split('\n')
result = []
in_new_block = False
for line in lines:
    # Detect the start of the new routes block
    if line.startswith('@finance_bp.route("/invoices/<int:inv_id>", methods=["PUT"])'):
        in_new_block = True
    
    if in_new_block:
        # Fix function body lines: 8-space -> 4-space
        stripped = line.lstrip()
        if stripped.startswith(('"""', "'")):
            result.append('    ' + stripped)
            continue
        if line.startswith('        ') and not stripped.startswith('"'):
            # Check if this is really function body (not a decorator)
            if not line.strip().startswith('@'):
                result.append('    ' + line[8:] if len(line) > 8 else line)
                continue
        # Fix comments that lost indentation
        if line.startswith('#') and not line.startswith('    #'):
            result.append('        ' + line)
            continue
    
    result.append(line)

# Use simpler approach for the block between the new routes (lines 136-260)
# The original file had flush() + commit() on separate lines
# Find and fix the flush+commit pattern
content2 = '\n'.join(result)
with open(path, 'w') as f:
    content2_clean = content2
with open('fix_result.txt', 'w') as fn:
    fn.write(f"done")

# Actually let me just use the re approach
pass