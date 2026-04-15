const CACHE_NAME = "tienda-cache-v1";

const urlsToCache = [
    "/",
    "/login",
    "/static/manifest.json"
];

// INSTALAR
self.addEventListener("install", event => {
    console.log("✅ PWA instalada");

    event.waitUntil(
        caches.open(CACHE_NAME)
            .then(cache => cache.addAll(urlsToCache))
    );
});

// ACTIVAR
self.addEventListener("activate", event => {
    console.log("🔄 Service Worker activo");
});

// FETCH (peticiones)
self.addEventListener("fetch", event => {
    event.respondWith(
        fetch(event.request)
            .catch(() => caches.match(event.request))
    );
});