/**
 * Harness target guard — refuse to drive anything that is not an isolated
 * loopback test server.
 *
 * Why (G1.26-B): the certification harnesses log in with a synthetic seeded
 * account. That account only exists in the throwaway database of
 * `scripts/test_server.py`, so the credentials themselves are harmless — the
 * real hazard is the *target*: `BASE` is an env override, and production
 * gunicorn also listens on loopback (127.0.0.1:5001). A typo there would point a
 * journey at the live application. (G1.25 recorded exactly that: one harness run
 * resolved a production URL and issued a single read-only GET before it was
 * caught.)
 *
 * So the guard is about the destination, not the password:
 *   - host must be 127.0.0.1 / localhost / ::1;
 *   - port must not be in the production range 5000–5010;
 *   - any parse failure is refused.
 *
 * It exits the process before a browser is launched, so a misconfigured run
 * makes no request at all.
 */

const LOOPBACK_HOSTS = new Set(['127.0.0.1', 'localhost', '::1', '[::1]']);
const PRODUCTION_PORTS = new Set([5000, 5001, 5002, 5003, 5004, 5005, 5006, 5007, 5008, 5009, 5010]);

function assertLoopback(name, url, envVar) {
  let parsed;
  try {
    parsed = new URL(url);
  } catch {
    console.error(`REFUSED: ${name} received an unparseable ${envVar} (${String(url).slice(0, 40)}).`);
    process.exit(1);
  }
  const host = parsed.hostname;
  const port = parsed.port ? Number(parsed.port) : (parsed.protocol === 'https:' ? 443 : 80);

  if (!LOOPBACK_HOSTS.has(host)) {
    console.error(
      `REFUSED: ${name} may only run against a loopback test server (${envVar} host=${host}). ` +
      'Start scripts/test_server.py on 127.0.0.1 and point the harness at it.',
    );
    process.exit(1);
  }
  if (PRODUCTION_PORTS.has(port)) {
    console.error(
      `REFUSED: ${name} may not target port ${port} — that is the production application range. ` +
        'Use an isolated test-server port (e.g. 51997–51999).',
    );
    process.exit(1);
  }
  return parsed;
}

module.exports = { assertLoopback, LOOPBACK_HOSTS, PRODUCTION_PORTS };
