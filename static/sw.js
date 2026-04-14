self.addEventListener("install", event => {
    console.log("PWA instalada");
});

self.addEventListener("fetch", event => {
    event.respondWith(fetch(event.request));
});