// service-worker.js
self.addEventListener('install', (e) => {
    e.waitUntil(
        caches.open('student-portal-v1').then((cache) => {
            return cache.addAll(['/', '/student/dashboard/']);
        })
    );
});

self.addEventListener('fetch', (e) => {
    e.respondWith(
        caches.match(e.request).then((response) => {
            return response || fetch(e.request);
        })
    );
});