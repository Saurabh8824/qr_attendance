const CACHE_NAME = 'student-portal-v3';
const ALL_PAGES = [
    '/attendance/student/dashboard/',
    '/attendance/student/timetable/',
    '/attendance/scan/',
    '/attendance/alerts/',
    '/attendance/student/profile/'
];

self.addEventListener('install', (e) => {
    e.waitUntil(
        caches.open(CACHE_NAME).then((cache) => {
            return cache.addAll(ALL_PAGES);
        })
    );
});

self.addEventListener('fetch', (e) => {
    e.respondWith(
        caches.match(e.request).then((cachedResponse) => {
            if (cachedResponse) return cachedResponse;

            return fetch(e.request).then((networkResponse) => {
                return caches.open(CACHE_NAME).then((cache) => {
                    cache.put(e.request, networkResponse.clone());
                    return networkResponse;
                });
            }).catch(() => {
                // Agar offline hai aur page cache mein nahi hai, to dashboard dikhayein
                return caches.match('/attendance/student/dashboard/');
            });
        })
    );
});
