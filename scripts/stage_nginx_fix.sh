#!/bin/bash
# Nginx/HTTPS — Certificate permission fix and reload
# Run: bash ~/stage_nginx_fix.sh
# This file is staged at a non-root location; you trigger the privileged commands.

echo "=== Step 1: Check cert files exist ==="
ls -la /etc/letsencrypt/live/shunyaos.com/fullchain.pem 2>/dev/null || echo "CERT FILE MISSING — may need certbot run first"

echo "=== Step 2: Fix group permissions (nginx needs to read) ==="
# The nginx user (www-data) needs read access to the letsencrypt directory
# Standard fix: setfacl or chgrp
sudo chgrp -R www-data /etc/letsencrypt/live/shunyaos.com/
sudo chgrp -R www-data /etc/letsencrypt/archive/shunyaos.com/
sudo chmod -R g+rX /etc/letsencrypt/live/shunyaos.com/
sudo chmod -R g+rX /etc/letsencrypt/archive/shunyaos.com/

echo "=== Step 3: Verify permissions ==="
sudo -u www-data test -r /etc/letsencrypt/live/shunyaos.com/fullchain.pem && echo "fullchain.pem READABLE" || echo "fullchain.pem STILL NOT READABLE"
sudo -u www-data test -r /etc/letsencrypt/live/shunyaos.com/privkey.pem && echo "privkey.pem READABLE" || echo "privkey.pem STILL NOT READABLE"

echo "=== Step 4: Test nginx config ==="
sudo nginx -t

echo "=== Step 5: Reload nginx ==="
sudo systemctl reload nginx

echo "=== Step 6: Verify HTTPS ==="
curl -fsSI https://shunyaos.com 2>&1 | head -5 || echo "HTTPS check — depends on DNS resolution"

echo "=== Done ==="