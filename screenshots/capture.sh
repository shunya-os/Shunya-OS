#!/bin/bash
BASE="http://localhost:5050"
OUT="."
SIZES=("1280x900" "768x1024" "375x812")
PAGES=(
  "/:landing"
  "/login:login"
  "/workspace/verify?email=hello%40example.com:verify"
  "/workspace/loading:loading"
  "/workspace/:workspace"
)

# Set a consistent window size for wkhtmltoimage
for page in "${PAGES[@]}"; do
  URL="${BASE}${page%%:*}"
  NAME="${page##*:}"
  for size in "${SIZES[@]}"; do
    W="${size%%x*}"
    H="${size##*x}"
    echo "Capturing ${NAME} at ${size}..."
    wkhtmltoimage --width "${W}" --height "${H}" --quality 85 --encoding UTF-8 "${URL}" "${OUT}/${NAME}_${W}x${H}.png" 2>/dev/null
  done
done

echo "Done capturing"
