const CACHE_NAME = 'systempay-v1';
const STATIC_ASSETS = [
  '/static/manifest.json',
  '/static/icons/icon-192.svg',
  '/static/icons/icon-512.svg',
  'https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap',
];

// Install — pre-cache static assets
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(STATIC_ASSETS);
    })
  );
  self.skipWaiting();
});

// Activate — clean old caches
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) => {
      return Promise.all(
        keys.filter((key) => key !== CACHE_NAME).map((key) => caches.delete(key))
      );
    })
  );
  self.clients.claim();
});

// Fetch — network-first for pages, cache-first for static
self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);

  // Skip non-GET requests
  if (request.method !== 'GET') return;

  // Skip Django admin
  if (url.pathname.startsWith('/admin/')) return;

  // Static assets and fonts — cache-first
  if (
    url.pathname.startsWith('/static/') ||
    url.hostname === 'fonts.googleapis.com' ||
    url.hostname === 'fonts.gstatic.com'
  ) {
    event.respondWith(
      caches.match(request).then((cached) => {
        if (cached) return cached;
        return fetch(request).then((response) => {
          if (response.ok) {
            const clone = response.clone();
            caches.open(CACHE_NAME).then((cache) => cache.put(request, clone));
          }
          return response;
        });
      })
    );
    return;
  }

  // HTML pages — network-first with offline fallback
  if (request.headers.get('Accept')?.includes('text/html')) {
    event.respondWith(
      fetch(request)
        .then((response) => {
          const clone = response.clone();
          caches.open(CACHE_NAME).then((cache) => cache.put(request, clone));
          return response;
        })
        .catch(() => {
          return caches.match(request).then((cached) => {
            if (cached) return cached;
            return new Response(
              `<!DOCTYPE html>
              <html lang="pt-BR">
              <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width,initial-scale=1">
                <title>Offline — SystemPay</title>
                <style>
                  *{margin:0;padding:0;box-sizing:border-box}
                  body{font-family:'Inter',system-ui,sans-serif;background:#0f172a;color:#f9fafb;display:flex;align-items:center;justify-content:center;min-height:100vh;padding:2rem;text-align:center}
                  .offline-icon{width:80px;height:80px;margin:0 auto 1.5rem;background:linear-gradient(135deg,#2563eb,#0ea5e9);border-radius:20px;display:flex;align-items:center;justify-content:center}
                  .offline-icon svg{width:40px;height:40px;fill:#fff}
                  h1{font-size:1.5rem;font-weight:700;margin-bottom:.5rem}
                  p{color:#94a3b8;font-size:.95rem;max-width:320px;margin:0 auto}
                  .btn{display:inline-block;margin-top:1.5rem;padding:.75rem 1.5rem;background:linear-gradient(135deg,#2563eb,#0ea5e9);color:#fff;border:none;border-radius:8px;font-size:.95rem;font-weight:600;cursor:pointer;text-decoration:none}
                </style>
              </head>
              <body>
                <div>
                  <div class="offline-icon">
                    <svg viewBox="0 0 24 24"><path d="M19.35 10.04C18.67 6.59 15.64 4 12 4c-1.48 0-2.85.43-4.01 1.17l1.46 1.46C10.21 6.23 11.08 6 12 6c3.04 0 5.5 2.46 5.5 5.5v.5H19c1.66 0 3 1.34 3 3 0 1.13-.64 2.11-1.56 2.62l1.45 1.45C23.16 18.16 24 16.68 24 15c0-2.64-2.05-4.78-4.65-4.96zM3 5.27l2.75 2.74C2.56 8.15 0 10.77 0 14c0 3.31 2.69 6 6 6h11.73l2 2 1.27-1.27L4.27 4 3 5.27zM7.73 10l8 8H6c-2.21 0-4-1.79-4-4s1.79-4 4-4h1.73z"/></svg>
                  </div>
                  <h1>Sem conexao</h1>
                  <p>Verifique sua internet e tente novamente. As paginas visitadas anteriormente podem estar disponiveis offline.</p>
                  <button class="btn" onclick="location.reload()">Tentar novamente</button>
                </div>
              </body>
              </html>`,
              { headers: { 'Content-Type': 'text/html; charset=utf-8' } }
            );
          });
        })
    );
    return;
  }

  // API/JSON — network only
  if (url.pathname.startsWith('/api/')) return;

  // Everything else — stale-while-revalidate
  event.respondWith(
    caches.match(request).then((cached) => {
      const fetchPromise = fetch(request).then((response) => {
        if (response.ok) {
          const clone = response.clone();
          caches.open(CACHE_NAME).then((cache) => cache.put(request, clone));
        }
        return response;
      });
      return cached || fetchPromise;
    })
  );
});
