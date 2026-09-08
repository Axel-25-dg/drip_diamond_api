/* ==========================================================================
   Service Worker: Notificaciones Push Nativas del Sistema Operativo
   Zapatillas EC - Drip Diamond Studio
   ========================================================================== */

self.addEventListener('install', (event) => {
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  event.waitUntil(self.clients.claim());
});

// Escuchar evento push entrante desde los servidores FCM / Apple / Mozilla / WebPush
self.addEventListener('push', (event) => {
  let data = {
    title: 'Zapatillas EC 👟',
    body: 'Tienes una nueva notificación en tu cuenta.',
    icon: '/static/img/icon-192.png',
    badge: '/static/img/badge-72.png',
    image: null,
    data: { url: '/' },
    vibrate: [200, 100, 200, 100, 200],
    renotify: true,
    tag: 'zapatillas-notification'
  };

  if (event.data) {
    try {
      const payload = event.data.json();
      data = { ...data, ...payload };
    } catch (e) {
      data.body = event.data.text();
    }
  }

  const options = {
    body: data.body,
    icon: data.icon || '/static/img/icon-192.png',
    badge: data.badge || '/static/img/badge-72.png',
    image: data.image || undefined,
    data: data.data || { url: '/' },
    vibrate: data.vibrate || [200, 100, 200],
    tag: data.tag || 'zapatillas-push-tag',
    renotify: data.renotify !== false,
    requireInteraction: true, // Mantener visible en la barra hasta que el usuario interactúe
    actions: data.actions || [
      { action: 'open_url', title: 'Ver Detalles 🚀' },
      { action: 'dismiss', title: 'Cerrar' }
    ]
  };

  event.waitUntil(
    self.registration.showNotification(data.title, options)
  );
});

// Escuchar el clic sobre la notificación del sistema
self.addEventListener('notificationclick', (event) => {
  event.notification.close();

  if (event.action === 'dismiss') {
    return;
  }

  const targetUrl = (event.notification.data && event.notification.data.url) ? event.notification.data.url : '/';

  event.waitUntil(
    clients.matchAll({ type: 'window', includeUncontrolled: true }).then((clientList) => {
      // Si la aplicación ya está abierta en una pestaña, enfocarla
      for (const client of clientList) {
        if (client.url.includes(self.location.origin) && 'focus' in client) {
          client.navigate(targetUrl);
          return client.focus();
        }
      }
      // Si no hay pestaña abierta, abrir una nueva ventana con la URL destino
      if (clients.openWindow) {
        return clients.openWindow(targetUrl);
      }
    })
  );
});
