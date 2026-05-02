// Service Worker for Web Push notifications
self.addEventListener('install', e => self.skipWaiting());
self.addEventListener('activate', e => e.waitUntil(self.clients.claim()));

self.addEventListener('push', event => {
  let data = {};
  try { data = event.data.json(); } catch (_) { data = { title: '推し提醒', body: event.data?.text() || '' }; }
  const title = data.title || '推し提醒';
  const options = {
    body: data.body || '',
    icon: data.icon || '/nijisanji-oshi/icon-192.png',
    badge: '/nijisanji-oshi/icon-192.png',
    tag: data.tag || 'oshi',
    data: { url: data.url || '/nijisanji-oshi/' },
    requireInteraction: false,
  };
  event.waitUntil(self.registration.showNotification(title, options));
});

self.addEventListener('notificationclick', event => {
  event.notification.close();
  const url = event.notification.data?.url || '/';
  event.waitUntil(
    clients.matchAll({ type: 'window' }).then(clientsList => {
      for (const c of clientsList) {
        if ('focus' in c) { c.navigate(url); return c.focus(); }
      }
      return clients.openWindow(url);
    })
  );
});
