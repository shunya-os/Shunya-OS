/**
 * SHUNYA OS — Service Worker
 * - Cache-first for static assets (JS, CSS, images, fonts)
 * - Network-first for API calls
 * - Notify user on update
 */

const CACHE_NAME = 'shunya-v1';
const STATIC_CACHE = 'shunya-static-v1';

// Assets to pre-cache on install
const PRECACHE_ASSETS = [
  '/',
  '/manifest.json',
];

// ── Install: pre-cache critical assets ──

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(STATIC_CACHE).then((cache) => {
      return cache.addAll(PRECACHE_ASSETS);
    }).then(() => {
      // Skip waiting so the new SW activates immediately
      return self.skipWaiting();
    })
  );
});

// ── Activate: clean up old caches and notify clients ──

self.addEventListener('activate', (event) => {
  const currentCaches = [CACHE_NAME, STATIC_CACHE];
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames
          .filter((name) => !currentCaches.includes(name))
          .map((name) => caches.delete(name))
      );
    }).then(() => {
      // Notify all clients that an update is available
      self.clients.matchAll().then((clients) => {
        clients.forEach((client) => {
          client.postMessage({ type: 'SW_UPDATED' });
        });
      });
      return self.clients.claim();
    })
  );
});

// ── Fetch: network-first for API, cache-first for static assets ──

self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);

  // API calls — network-first strategy
  if (url.pathname.startsWith('/api/')) {
    event.respondWith(networkFirst(request));
    return;
  }

  // Static assets — cache-first strategy (JS, CSS, images, fonts)
  if (
    request.destination === 'script' ||
    request.destination === 'style' ||
    request.destination === 'image' ||
    request.destination === 'font' ||
    /\.(js|css|png|jpg|jpeg|gif|svg|webp|ico|woff2?|ttf|eot)$/i.test(url.pathname)
  ) {
    event.respondWith(cacheFirst(request));
    return;
  }

  // Navigation requests — network-first with cache fallback
  if (request.mode === 'navigate') {
    event.respondWith(networkFirst(request));
    return;
  }

  // Everything else — network-first
  event.respondWith(networkFirst(request));
});

// ── Strategies ──

async function networkFirst(request) {
  try {
    const response = await fetch(request);
    // Cache successful responses (GET only)
    if (request.method === 'GET' && response.ok) {
      const cache = await caches.open(CACHE_NAME);
      cache.put(request, response.clone());
    }
    return response;
  } catch (err) {
    const cached = await caches.match(request);
    if (cached) {
      return cached;
    }
    // Return a minimal offline fallback for navigation requests
    if (request.mode === 'navigate') {
      return new Response(
        '<!DOCTYPE html><html><head><title>Offline</title><meta name="viewport" content="width=device-width,initial-scale=1"><style>body{font-family:sans-serif;display:flex;align-items:center;justify-content:center;height:100vh;background:#FAF8F5;color:#1A1C1D;text-align:center;padding:20px;margin:0}h1{font-weight:300;font-size:24px}</style></head><body><h1>SHUNYA is offline.<br>Please check your connection.</h1></body></html>',
        { headers: { 'Content-Type': 'text/html; charset=utf-8' } }
      );
    }
    return new Response('Offline', { status: 503 });
  }
}

async function cacheFirst(request) {
  const cached = await caches.match(request);
  if (cached) {
    return cached;
  }
  try {
    const response = await fetch(request);
    if (request.method === 'GET' && response.ok) {
      const cache = await caches.open(STATIC_CACHE);
      cache.put(request, response.clone());
    }
    return response;
  } catch (err) {
    return new Response('Offline', { status: 503 });
  }
}