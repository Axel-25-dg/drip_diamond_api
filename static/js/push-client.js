/**
 * Zapatillas EC - Push Notification Client SDK
 * Permite suscribir fácilmente cualquier dispositivo/navegador a las notificaciones Push nativas.
 */
class ZapatillasPushClient {
  constructor(options = {}) {
    this.apiBase = options.apiBase || '/api/tienda/push';
    this.serviceWorkerUrl = options.serviceWorkerUrl || '/static/sw-push.js';
    this.token = options.token || null;
  }

  // Convierte la llave VAPID base64 en un Uint8Array para el navegador
  urlBase64ToUint8Array(base64String) {
    const padding = '='.repeat((4 - (base64String.length % 4)) % 4);
    const base64 = (base64String + padding).replace(/-/g, '+').replace(/_/g, '/');
    const rawData = window.atob(base64);
    const outputArray = new Uint8Array(rawData.length);
    for (let i = 0; i < rawData.length; ++i) {
      outputArray[i] = rawData.charCodeAt(i);
    }
    return outputArray;
  }

  // Verifica si el navegador soporta Notificaciones Push del sistema
  isSupported() {
    return ('serviceWorker' in navigator) && ('PushManager' in window) && ('Notification' in window);
  }

  // Obtiene el estado actual de permiso ('granted', 'denied', 'default')
  getPermissionState() {
    if (!this.isSupported()) return 'unsupported';
    return Notification.permission;
  }

  // Solicita permiso al usuario y suscribe el dispositivo al backend
  async solicitarYRegistrar() {
    if (!this.isSupported()) {
      throw new Error('El navegador no soporta Notificaciones Push Nativas.');
    }

    const permission = await Notification.requestPermission();
    if (permission !== 'granted') {
      throw new Error('El usuario no concedió permiso para las notificaciones.');
    }

    // 1. Registrar el Service Worker
    const registration = await navigator.serviceWorker.register(this.serviceWorkerUrl, { scope: '/' });
    await navigator.serviceWorker.ready;

    // 2. Obtener la clave pública VAPID desde el Backend Django
    const vapidRes = await fetch(`${this.apiBase}/vapid-key/`);
    const vapidData = await vapidRes.json();
    if (!vapidData.success) {
      throw new Error('No se pudo obtener la clave pública VAPID del servidor.');
    }

    const applicationServerKey = this.urlBase64ToUint8Array(vapidData.data.vapid_public_key);

    // 3. Suscribir el dispositivo en el PushManager del navegador
    let subscription = await registration.pushManager.getSubscription();
    if (!subscription) {
      subscription = await registration.pushManager.subscribe({
        userVisibleOnly: true,
        applicationServerKey: applicationServerKey
      });
    }

    const subJson = subscription.toJSON();

    // 4. Enviar la suscripción a la API Django (/api/tienda/push/suscribir/)
    const headers = { 'Content-Type': 'application/json' };
    if (this.token) {
      headers['Authorization'] = `Bearer ${this.token}`;
    }

    const response = await fetch(`${this.apiBase}/suscribir/`, {
      method: 'POST',
      headers: headers,
      body: JSON.stringify({
        endpoint: subJson.endpoint,
        keys: subJson.keys,
        user_agent: navigator.userAgent
      })
    });

    const resData = await response.json();
    return resData;
  }
}

// Exportar globalmente y como módulo si aplica
if (typeof window !== 'undefined') {
  window.ZapatillasPushClient = ZapatillasPushClient;
}
