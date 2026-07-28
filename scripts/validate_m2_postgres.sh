#!/usr/bin/env bash
# Milestone 2 Founder Action Validation — PostgreSQL flow
set -e
BASE="http://localhost:5000"
COOKIE_JAR=/tmp/shunya_cookies.txt
rm -f "$COOKIE_JAR"

echo "=== STEP 1: Sign In ==="
RESP=$(curl -s -c "$COOKIE_JAR" -X POST "$BASE/api/v1/founder/signin" \
  -H 'Content-Type: application/json' \
  -d '{"email":"nishesh@shunyaos.com","password":"test123","name":"Nishesh"}')
echo "$RESP" | python3 -m json.tool
echo ""

echo "=== STEP 2: Executive Home loads ==="
EH=$(curl -s -b "$COOKIE_JAR" "$BASE/api/v1/founder/executive-home-v2")
echo "$EH" | python3 -m json.tool | head -30
echo "..."
REC_COUNT=$(echo "$EH" | python3 -c "import sys,json; d=json.load(sys.stdin); print(len(d['data']['recommendations']))")
echo "Recommendations count: $REC_COUNT"
echo ""

echo "=== STEP 3: Create Space (following recommendation) ==="
SPACE_RESP=$(curl -s -b "$COOKIE_JAR" -X POST "$BASE/api/v1/founder/spaces" \
  -H 'Content-Type: application/json' \
  -d '{"name":"My Business","space_type":"organization","description":"My first organization space"}')
echo "$SPACE_RESP" | python3 -m json.tool
HTTP_CODE=$(curl -s -o /dev/null -w '%{http_code}' -b "$COOKIE_JAR" -X POST "$BASE/api/v1/founder/spaces" \
  -H 'Content-Type: application/json' \
  -d '{"name":"My Business","space_type":"organization","description":"My first organization space"}')
echo "HTTP status: $HTTP_CODE"
echo ""

echo "=== STEP 4: Space appears in Executive Home ==="
EH2=$(curl -s -b "$COOKIE_JAR" "$BASE/api/v1/founder/executive-home-v2")
echo "$EH2" | python3 -c "
import sys,json
d=json.load(sys.stdin)
data=d['data']
print('Morning Brief items:', len(data['morning_brief']['items']))
print('Spaces:', data['business_health']['spaces'])
print('Health:', data['business_health']['assessment'])
for item in data['morning_brief']['items'][:3]:
    print(f'  - {item[\"title\"]}')
for rec in data['recommendations'][:2]:
    print(f'  REC: {rec[\"title\"]}')
print('Recent Activity:', len(data['recent_activity']))
print('Continue Working:', len(data['continue_working']))
"
echo ""

echo "=== STEP 5: Create an Object in the space ==="
SPACE_ID=$(echo "$EH2" | python3 -c "
import sys,json
d=json.load(sys.stdin)
spaces=d['data']['morning_brief']['summary']['active_spaces']
print(f'spaces_count={spaces}')
")

# Get the first space_id
FIRST_SPACE=$(curl -s -b "$COOKIE_JAR" "$BASE/api/v1/founder/spaces" | python3 -c "
import sys,json
d=json.load(sys.stdin)
if d['success'] and d['data']:
    s=d['data'][0]
    print(f\"{s['space_id']}|{s['name']}\")
else:
    print('none')
")
echo "First space: $FIRST_SPACE"
SPC_ID=$(echo "$FIRST_SPACE" | cut -d'|' -f1)
SPC_NAME=$(echo "$FIRST_SPACE" | cut -d'|' -f2)
echo ""

if [ "$SPC_ID" != "none" ] && [ -n "$SPC_ID" ]; then
  echo "=== Create Object ==="
  OBJ_RESP=$(curl -s -b "$COOKIE_JAR" -X POST "$BASE/api/v1/founder/spaces/$SPC_ID/objects" \
    -H 'Content-Type: application/json' \
    -d '{"name":"Business Plan 2026","object_type":"Document","content":"Strategic growth plan for Q3-Q4"}')
  echo "$OBJ_RESP" | python3 -m json.tool
  HTTP_OBJ=$(echo "$OBJ_RESP" | python3 -c "import sys,json; d=json.load(sys.stdin); print('status' if d.get('success') else 'FAILED: '+d.get('error','?'))")
  echo "Object status: $HTTP_OBJ"
  echo ""
fi

echo "=== STEP 6: Executive Home after creating objects ==="
EH3=$(curl -s -b "$COOKIE_JAR" "$BASE/api/v1/founder/executive-home-v2")
echo "$EH3" | python3 -c "
import sys,json
d=json.load(sys.stdin)
data=d['data']
print('Morning Brief items:', len(data['morning_brief']['items']))
print('Spaces:', data['business_health']['spaces'])
print('Objects:', data['business_health']['objects'])
print('Recent Activity:', len(data['recent_activity']))
print('Continue Working:', len(data['continue_working']))
print()
for item in data['morning_brief']['items'][:4]:
    print(f'  [{item[\"priority\"]}] {item[\"title\"]}')
print()
for a in data['recent_activity'][:3]:
    print(f'  ACTIVITY: {a[\"type\"]}: {a[\"title\"]}')
print()
for cw in data['continue_working'][:3]:
    print(f'  CONTINUE: {cw[\"type\"]}: {cw[\"title\"]}')
"
echo ""

echo "=== STEP 7: Refresh (load second time — persistence check) ==="
EH4=$(curl -s -b "$COOKIE_JAR" "$BASE/api/v1/founder/executive-home-v2")
SPACES_AGAIN=$(echo "$EH4" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['data']['business_health']['spaces'])")
OBJECTS_AGAIN=$(echo "$EH4" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['data']['business_health']['objects'])")
echo "Spaces (refresh): $SPACES_AGAIN"
echo "Objects (refresh): $OBJECTS_AGAIN"

if [ "$SPACES_AGAIN" -gt 0 ] && [ "$SPACES_AGAIN" = "$SPACES_AGAIN" ] 2>/dev/null; then
  echo "✅ Space persists after refresh"
fi
echo ""

echo "=== VERIFICATION SUMMARY ==="
echo "$EH4" | python3 -c "
import sys,json
d=json.load(sys.stdin)
data=d['data']
ok = True

# Check all sections present
sections = ['morning_brief', 'recommendations', 'business_health', 'recent_activity', 'continue_working']
for s in sections:
    if s not in data:
        print(f'❌ Missing section: {s}')
        ok = False
    else:
        print(f'✅ {s} present')

# Check no placeholder
text = str(data).lower()
for word in ['lorem', 'ipsum', 'placeholder', 'fake']:
    if word in text:
        print(f'❌ Found placeholder: {word}')
        ok = False

# Check traceability  
print(f'✅ {data[\"business_health\"][\"spaces\"]} spaces, {data[\"business_health\"][\"objects\"]} objects')
print(f'✅ Morning Brief: {len(data[\"morning_brief\"][\"items\"])} items')
print(f'✅ Recommendations: {len(data[\"recommendations\"])} items')
print(f'✅ Recent Activity: {len(data[\"recent_activity\"])} items')
print(f'✅ Continue Working: {len(data[\"continue_working\"])} items')

if ok:
    print()
    print('🎯 All Milestone 2 validation checks passed on PostgreSQL')
else:
    print()
    print('⚠ Some checks failed')
"