// SM News — Service Worker
// App-shell caches for offline use; news.json & weather always fetched fresh from network.

const CACHE_NAME = 'sm-news-shell-v1';
const APP_SHELL = [
  './',
  './index.html',
  './manifest.json',
  './icons/icon-72.png',
  './icons/icon-96.png',
  './icons/icon-128.png',
  './icons/icon-144.png',
  './icons/icon-152.png',
  './icons/icon-192.png',
  './icons/icon-384.png',
  './icons/icon-512.png'
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => cache.addAll(APP_SHELL))
      .then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((k) => k !== CACHE_NAME).map((k) => caches.delete(k)))
    ).then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', (event) => {
  const req = event.request;
  const url = new URL(req.url);

  if (req.method !== 'GET') return;

  // Never cache live data — news.json, weather API, or any cross-origin API calls.
  if (url.pathname.endsWith('news.json') || url.hostname.includes('open-meteo.com')) {
    event.respondWith(fetch(req).catch(() => caches.match(req)));
    return;
  }

  // App shell: cache-first, falling back to network, then updating the cache.
  event.respondWith(
    caches.match(req).then((cached) => {
      const fetchPromise = fetch(req).then((res) => {
        if (res && res.ok && url.origin === self.location.origin) {
          const clone = res.clone();
          caches.open(CACHE_NAME).then((cache) => cache.put(req, clone));
        }
        return res;
      }).catch(() => cached);
      return cached || fetchPromise;
    })
  );
});
