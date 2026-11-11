const CACHE_NAME = 'vilacircula-v47';
const APP_FILES = ['./', './index.html', './legal.html', './legal.css?v=1', './i18n.js?v=7', './accessibility.css?v=2', './manifest.json?v=2', './api-config.json?v=3', './icons/icon.svg', './icons/boot-mark.png', './icons/boot-print-192.png', './icons/boot-print-512.png', './icons/boot-print-maskable-512.png', './icons/icon-192.png', './icons/icon-512.png', './viladecans.js', './viladecans.css', './features.css?v=3', './api-client.js?v=37', './api-client.css?v=30', './cashier.css', './cashier-dashboard.css', './cashier-rewards.css?v=3'];

self.addEventListener('install', event => {
  event.waitUntil(caches.open(CACHE_NAME).then(cache => cache.addAll(APP_FILES)).then(() => self.skipWaiting()));
});

self.addEventListener('activate', event => {
  event.waitUntil(caches.keys().then(keys => Promise.all(
    keys.filter(key => key !== CACHE_NAME).map(key => caches.delete(key))
  )));
  self.clients.claim();
});

self.addEventListener('fetch', event => {
  const requestUrl = new URL(event.request.url);
  if (event.request.method !== 'GET') return;
  if (requestUrl.origin !== self.location.origin) return;
  if (requestUrl.pathname.startsWith('/api/')) {
    event.respondWith(fetch(event.request).catch(() => caches.match('./index.html')));
    return;
  }
  if (requestUrl.pathname.startsWith('/icons/')) {
    event.respondWith(caches.match(event.request).then(cached => cached || fetch(event.request).then(response => {
      const copy = response.clone();
      caches.open(CACHE_NAME).then(cache => cache.put(event.request, copy));
      return response;
    }).catch(() => caches.match('./index.html'))));
    return;
  }
  event.respondWith(caches.match(event.request).then(cached => cached || fetch(event.request).then(response => {
    const copy = response.clone();
    caches.open(CACHE_NAME).then(cache => cache.put(event.request, copy));
    return response;
  }).catch(() => caches.match('./index.html'))));
});

self.addEventListener('message', event => {
  if (event.data && event.data.type === 'SKIP_WAITING') self.skipWaiting();
});
