// TripSync Service Worker v4 — Zero-Downtime PWA
// Strategy: Cache-first for static assets, network-first for HTML pages
// API calls always go to network (no caching of search results)

const CACHE_NAME = 'tripsync-v6';
const STATIC_ASSETS = [
  '/',
  '/index.html',
  '/planner.html',
  '/privacy.html',
  '/terms.html',
  '/manifest.json',
  '/icon.png',
  '/icon-badge.png',
  '/icon-192.png',
  '/apple-touch-icon.png',
  '/favicon.png'
];

// Install — pre-cache all static assets
self.addEventListener('install', (e) => {
  e.waitUntil(
    caches.open(CACHE_NAME).then(cache => cache.addAll(STATIC_ASSETS))
  );
  self.skipWaiting(); // Activate immediately
});

// Activate — clean up old caches
self.addEventListener('activate', (e) => {
  e.waitUntil(
    caches.keys().then(keys =>
      Promise.all(keys.map(k => { if (k !== CACHE_NAME) return caches.delete(k); }))
    )
  );
  self.clients.claim();
});

// Fetch — smart routing strategy
self.addEventListener('fetch', (e) => {
  // Ignore chrome-extension://, moz-extension://, etc.
  if (!e.request.url.startsWith('http://') && !e.request.url.startsWith('https://')) {
    return;
  }

  const url = new URL(e.request.url);

  // Never intercept API calls — always go to network for fresh data
  if (url.pathname.startsWith('/api/')) {
    return; // Pass through directly
  }

  // For navigation (HTML pages) — network-first, fall back to cache
  if (e.request.mode === 'navigate') {
    e.respondWith(
      fetch(e.request)
        .then(resp => {
          // Update cache with fresh version
          const clone = resp.clone();
          caches.open(CACHE_NAME).then(cache => cache.put(e.request, clone));
          return resp;
        })
        .catch(() => caches.match(e.request).then(cached => cached || caches.match('/index.html')))
    );
    return;
  }

  // For static assets (fonts, images, scripts) — cache-first, then network
  e.respondWith(
    caches.match(e.request).then(cached => {
      if (cached) return cached;
      return fetch(e.request).then(resp => {
        // Cache successful static responses
        if (resp && resp.status === 200 && resp.type !== 'opaque') {
          const clone = resp.clone();
          caches.open(CACHE_NAME).then(cache => cache.put(e.request, clone));
        }
        return resp;
      }).catch(() => cached || new Response('', { status: 503 }));
    })
  );
});
