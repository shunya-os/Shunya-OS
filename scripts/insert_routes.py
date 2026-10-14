import sys

path = sys.argv[1]

with open(path) as f:
    content = f.read()

marker = '    return jsonify({"invoice": inv.to_dict()}), 201\n\n@finance_bp.route("/invoices", methods=["GET"])'

# Read the routes template
import os
template_path = os.path.join(os.path.dirname(__file__), 'finance_routes_template.py')
with open(template_path) as f:
    new_routes = f.read()

if marker in content:
    content = content.replace(marker, new_routes)
    with open(path, 'w') as f:
        f.write(content)
    print("OK: routes inserted")
else:
    print("ERROR: marker not found")
    # Debug: show context around where we expected the marker
    idx = content.find('return jsonify({"invoice": inv.to_dict()}), 201')
    if idx >= 0:
        print("Found return line, showing context...")
        print(content[idx:idx+200])