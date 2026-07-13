const CACHE = 'shunya-v1';
const SHELL = ['/', '/static/shunya.css?v=13', '/static/icon-192.svg', '/static/icon-512.svg', '/static/manifest.json'];

self.addEventListener('install', e => {
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(SHELL)));
  self.skipWaiting();
});

self.addEventListener('activate', e => {
  e.waitUntil(caches.keys().then(ks => Promise.all(ks.filter(k => k !== CACHE).map(k => caches.delete(k)))));
  self.clients.claim();
});

self.addEventListener('fetch', e => {
  const url = new URL(e.request.url);
  // HTML pages: network-first, fallback to cache
  if (url.pathname === '/' || url.pathname.startsWith('/auth/')) {
    e.respondWith(
      fetch(e.request).catch(() => caches.match(e.request).then(r => r || caches.match('/')))
    );
    return;
  }
  // Static assets: cache-first
  if (url.pathname.startsWith('/static/')) {
    e.respondWith(
      caches.match(e.request).then(r => r || fetch(e.request).then(res => { caches.open(CACHE).then(c => c.put(e.request, res.clone())); return res; }))
    );
    return;
  }
  // Everything else: network, cache on success
  e.respondWith(
    fetch(e.request).then(res => {
      if (res.ok) caches.open(CACHE).then(c => c.put(e.request, res.clone()));
      return res;
    }).catch(() => caches.match(e.request))
  );
});