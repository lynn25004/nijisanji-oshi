// Service Worker：Web Push + 離線基本資源快取
const CACHE_NAME = 'oshi-v5';
const CORE = [
  './',
  './index.html',
  './manifest.json',
  './icon-192.png',
  './icon-512.png',
  './apple-touch-icon.png',
  './data/members.json',
];

self.addEventListener('install', e => {
  e.waitUntil(caches.open(CACHE_NAME).then(c => c.addAll(CORE).catch(() => {})));
  self.skipWaiting();
});

self.addEventListener('activate', e => {
  e.waitUntil(
    caches.keys().then(keys =>
      Promise.all(keys.filter(k => k !== CACHE_NAME).map(k => caches.delete(k)))
    ).then(() => self.clients.claim())
  );
});

// Network-first for HTML, cache-first for static (避免使用者被舊 HTML 卡住)
self.addEventListener('fetch', e => {
  const req = e.request;
  if (req.method !== 'GET') return;
  const url = new URL(req.url);

  // 跨 origin 不接管（Holodex / Supabase / Resend / YouTube 圖等都讓它正常走）
  if (url.origin !== location.origin) return;

  if (req.mode === 'navigate' || req.headers.get('accept')?.includes('text/html')) {
    e.respondWith(
      fetch(req).catch(() => caches.match(req).then(c => c || caches.match('./index.html')))
    );
    return;
  }

  // 靜態資源 cache-first
  e.respondWith(
    caches.match(req).then(c => c || fetch(req).then(resp => {
      if (resp.ok) caches.open(CACHE_NAME).then(cc => cc.put(req, resp.clone()));
      return resp;
    }))
  );
});

self.addEventListener('push', event => {
  let data = {};
  try { data = event.data.json(); } catch (_) { data = { title: '推し提醒', body: event.data?.text() || '' }; }
  const title = data.title || '推し提醒';
  const options = {
    body: data.body || '',
    icon: data.icon || './icon-192.png',
    badge: './icon-192.png',
    tag: data.tag || 'oshi',
    data: { url: data.url || './' },
    requireInteraction: false,
  };
  event.waitUntil(self.registration.showNotification(title, options));
});

self.addEventListener('notificationclick', event => {
  event.notification.close();
  const url = event.notification.data?.url || './';
  event.waitUntil(
    clients.matchAll({ type: 'window' }).then(clientsList => {
      for (const c of clientsList) {
        if ('focus' in c) { c.navigate(url); return c.focus(); }
      }
      return clients.openWindow(url);
    })
  );
});
