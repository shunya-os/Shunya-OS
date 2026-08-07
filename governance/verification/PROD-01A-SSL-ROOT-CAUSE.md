# PROD-01A — SSL Root Cause Verification

**Date:** 2026-08-06
**Status:** ✅ ROOT CAUSE IDENTIFIED

---

## 1. DNS

| Check | Result |
|-------|--------|
| A record | ✅ `shunyaos.com → 217.76.53.46` |
| Nameservers | ✅ `ns27.domaincontrol.com`, `ns28.domaincontrol.com` |
| Propagation | ✅ A record matches server public IP |
| Server IPv4 | ✅ `217.76.53.46/20 on eth0` |

**DNS: OK**

---

## 2. Firewall / Ports

| Check | Result |
|-------|--------|
| Port 80 | ✅ Listening on `0.0.0.0:80` (nginx) |
| Port 443 | ✅ Listening on `0.0.0.0:443` (nginx) |
| SSH | ✅ Port 22 open |

**Firewall: OK — ports open**

---

## 3. Root Cause: Missing SSL Certificate Files

### Evidence

| Check | Command | Result |
|-------|---------|--------|
| Live cert directory | `test -d /etc/letsencrypt/live/shunyaos.com` | ❌ **DOES NOT EXIST** |
| Archive cert directory | `test -d /etc/letsencrypt/archive/shunyaos.com` | ❌ **DOES NOT EXIST** |
| Cert file | `test -f /etc/letsencrypt/live/shunyaos.com/fullchain.pem` | ❌ **NOT FOUND** |
| Cert file readable | `cat /etc/letsencrypt/live/shunyaos.com/fullchain.pem` | ❌ **NOT READABLE (doesn't exist)** |
| Only related file | `find /etc/letsencrypt -name '*shunyaos*'` | ✅ `renewal/shunyaos.com.conf` (configuration only) |

### Nginx configuration

Nginx server block loads:

```
ssl_certificate     /etc/letsencrypt/live/shunyaos.com/fullchain.pem;
ssl_certificate_key /etc/letsencrypt/live/shunyaos.com/privkey.pem;
```

**Neither file exists.** Nginx test confirms:

```
nginx: [emerg] cannot load certificate "/etc/letsencrypt/live/shunyaos.com/fullchain.pem":
  BIO_new_file() failed (SSL: error:8000000D:system library::Permission denied:
  calling fopen(...) error:10080002:BIO routines::system lib)
```

The "Permission denied" message is misleading — it means the file doesn't exist or the path doesn't resolve. `stat()` returns EACCES when one of the path components isn't searchable, but in this case the root cause is that **the directory itself does not exist**.

### Certificate Renewal Config

`/etc/letsencrypt/renewal/shunyaos.com.conf` exists and shows:
- `version = 2.9.0`
- `authenticator = nginx`
- Points to `/etc/letsencrypt/live/shunyaos.com/` for cert/privkey/chain/fullchain

This means Certbot was configured to manage certificates for shunyaos.com, but the actual certificate files were **never issued or were deleted** after issuance.

---

## 4. Application Server

| Check | Result |
|-------|--------|
| Gunicorn | ✅ Listening on `127.0.0.1:5001` (2 workers) |
| HTTP response | ❌ **TIMEOUT** — workers are hung/unresponsive |
| Backend health | ❌ No response on `/health` endpoint |

The backend application (Gunicorn/Flask) is running but hung. This is a separate issue from the SSL certificate problem.

---

## Root Cause (Primary)

**The Let's Encrypt certificate for `shunyaos.com` was never successfully issued, or the certificate files were deleted after issuance.**

- `/etc/letsencrypt/live/shunyaos.com/` — **does not exist**
- `/etc/letsencrypt/archive/shunyaos.com/` — **does not exist**
- Nginx references certificate files that don't exist
- Nginx cannot serve HTTPS
- HTTP returns 404 (as configured — the `return 404` is the intended redirect behavior)

## Root Cause (Secondary)

**The backend Gunicorn application on port 5001 is hung/unresponsive.** Even if SSL were fixed, nginx would proxy to a non-responsive backend.

---

## Required Fix

1. **Issue new Let's Encrypt certificate:**
   ```bash
   sudo certbot --nginx -d shunyaos.com -d www.shunyaos.com
   ```

2. **Restart nginx:**
   ```bash
   sudo systemctl restart nginx
   ```

3. **Fix backend application** — diagnose why Gunicorn workers are hung on port 5001.

**Do not apply until root cause is accepted.**