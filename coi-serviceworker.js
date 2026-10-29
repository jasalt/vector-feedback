/* Scoped cross-origin isolation for static Pages hosting.
 * Adapted from the sibling Jolt Wasm experiment's EXP-018 deployment.
 * No caching: updated runtime files are fetched from the server.
 */
self.addEventListener('install', event => event.waitUntil(self.skipWaiting()));
self.addEventListener('activate', event => event.waitUntil(self.clients.claim()));
self.addEventListener('fetch', event => {
  if (event.request.method !== 'GET') return;
  if (event.request.cache === 'only-if-cached' && event.request.mode !== 'same-origin') return;
  event.respondWith(fetch(event.request).then(response => {
    if (response.type === 'opaque' || response.status === 0) return response;
    const headers = new Headers(response.headers);
    headers.set('Cross-Origin-Embedder-Policy', 'require-corp');
    headers.set('Cross-Origin-Opener-Policy', 'same-origin');
    if (new URL(event.request.url).pathname.endsWith('.wasm'))
      headers.set('Content-Type', 'application/wasm');
    return new Response(response.body, {
      status: response.status, statusText: response.statusText, headers
    });
  }));
});
