/**
 * Enhanced Service Worker for MINGUS
 * Optimized for African American professionals on varying network speeds
 * Offline-first approach with aggressive caching for 3G networks
 */

const CACHE_VERSION = 'mingus-v1.2.0';
const STATIC_CACHE = 'mingus-static-v1.2.0';
const DATA_CACHE = 'mingus-data-v1.2.0';
const OFFLINE_CACHE = 'mingus-offline-v1.2.0';

// Essential resources for offline functionality
const ESSENTIAL_RESOURCES = [
    '/',
    '/index.html',
    '/css/critical.css',
    '/js/mobile-performance-optimizer.js',
    '/js/financial-calculator-worker.js',
    '/images/logo.webp',
    '/images/logo-fallback.jpg',
    '/offline.html',
    '/manifest.json'
];

// Financial data resources (cached for offline calculations)
const FINANCIAL_DATA_RESOURCES = [
    '/api/salary-data',
    '/api/industry-data',
    '/api/tax-brackets',
    '/api/cost-of-living',
    '/api/equity-factors'
];

// Progressive loading resources (loaded based on network)
const PROGRESSIVE_RESOURCES = {
    '3g': [
        '/css/non-critical-minimal.css',
        '/js/core-functions.js'
    ],
    '4g': [
        '/css/non-critical.css',
        '/js/analytics.js',
        '/js/social-sharing.js',
        '/images/hero.webp',
        '/images/features.webp'
    ]
};

// Network-aware cache strategies
const CACHE_STRATEGIES = {
    '3g': {
        maxCacheSize: 25 * 1024 * 1024, // 25MB
        cacheDuration: 7 * 24 * 60 * 60 * 1000, // 7 days
        prefetchLimit: 2,
        imageQuality: 'low'
    },
    '4g': {
        maxCacheSize: 50 * 1024 * 1024, // 50MB
        cacheDuration: 14 * 24 * 60 * 60 * 1000, // 14 days
        prefetchLimit: 5,
        imageQuality: 'high'
    }
};

// Install event - cache essential resources
self.addEventListener('install', (event) => {
    console.log('Service Worker: Installing enhanced version...');
    
    event.waitUntil(
        Promise.all([
            // Cache essential resources immediately
            caches.open(STATIC_CACHE).then(cache => {
                console.log('Caching essential resources for offline functionality');
                return cache.addAll(ESSENTIAL_RESOURCES);
            }),
            
            // Cache financial data for offline calculations
            caches.open(DATA_CACHE).then(cache => {
                console.log('Caching financial data for offline calculations');
                return cache.addAll(FINANCIAL_DATA_RESOURCES);
            })
        ]).then(() => {
            console.log('Essential resources cached successfully');
            return self.skipWaiting();
        }).catch(error => {
            console.error('Failed to cache essential resources:', error);
        })
    );
});

// Activate event - clean up old caches
self.addEventListener('activate', (event) => {
    console.log('Service Worker: Activating enhanced version...');
    
    event.waitUntil(
        caches.keys().then(cacheNames => {
            return Promise.all(
                cacheNames.map(cacheName => {
                    if (cacheName !== STATIC_CACHE && 
                        cacheName !== DATA_CACHE && 
                        cacheName !== OFFLINE_CACHE &&
                        !cacheName.startsWith('mingus-')) {
                        console.log('Deleting old cache:', cacheName);
                        return caches.delete(cacheName);
                    }
                })
            );
        }).then(() => {
            console.log('Old caches cleaned up');
            return self.clients.claim();
        })
    );
});

// Fetch event - network-aware caching strategy
self.addEventListener('fetch', (event) => {
    const { request } = event;
    const url = new URL(request.url);
    
    // Skip non-GET requests
    if (request.method !== 'GET') {
        return;
    }
    
    // Handle different types of requests
    if (url.pathname.startsWith('/api/')) {
        event.respondWith(handleApiRequest(request));
    } else if (request.destination === 'image') {
        event.respondWith(handleImageRequest(request));
    } else if (request.destination === 'document') {
        event.respondWith(handleDocumentRequest(request));
    } else {
        event.respondWith(handleStaticRequest(request));
    }
});

// Handle API requests with offline data fallback
async function handleApiRequest(request) {
    const url = new URL(request.url);
    
    try {
        // Try network first for API requests
        const networkResponse = await fetch(request);
        
        if (networkResponse.ok) {
            // Cache successful API responses
            const cache = await caches.open(DATA_CACHE);
            cache.put(request, networkResponse.clone());
            
            // Store data for offline use
            if (url.pathname.startsWith('/api/salary-data') || 
                url.pathname.startsWith('/api/industry-data')) {
                storeOfflineData(url.pathname, await networkResponse.clone().json());
            }
            
            return networkResponse;
        }
    } catch (error) {
        console.log('Network request failed, trying cache:', error);
    }
    
    // Fallback to cached data
    const cache = await caches.open(DATA_CACHE);
    const cachedResponse = await cache.match(request);
    
    if (cachedResponse) {
        return cachedResponse;
    }
    
    // Return mock data for offline functionality
    return new Response(JSON.stringify(getMockApiData(url.pathname)), {
        headers: { 'Content-Type': 'application/json' }
    });
}

// Handle image requests with quality optimization
async function handleImageRequest(request) {
    const url = new URL(request.url);
    const networkInfo = await getNetworkInfo();
    
    try {
        // Try cache first for images
        const cache = await caches.open(STATIC_CACHE);
        const cachedResponse = await cache.match(request);
        
        if (cachedResponse) {
            // Update cache in background if network is available
            if (networkInfo.effectiveType !== 'offline') {
                fetch(request).then(response => {
                    if (response.ok) {
                        cache.put(request, response);
                    }
                }).catch(() => {
                    // Ignore background update failures
                });
            }
            
            return cachedResponse;
        }
        
        // Fetch from network if not cached
        const networkResponse = await fetch(request);
        
        if (networkResponse.ok) {
            // Cache the image
            cache.put(request, networkResponse.clone());
            return networkResponse;
        }
    } catch (error) {
        console.log('Image fetch failed:', error);
    }
    
    // Return placeholder image for offline
    return caches.match('/images/placeholder.webp');
}

// Handle document requests (HTML pages)
async function handleDocumentRequest(request) {
    const url = new URL(request.url);
    
    try {
        // Try network first for documents
        const networkResponse = await fetch(request);
        
        if (networkResponse.ok) {
            // Cache successful responses
            const cache = await caches.open(STATIC_CACHE);
            cache.put(request, networkResponse.clone());
            return networkResponse;
        }
    } catch (error) {
        console.log('Document fetch failed, serving offline page:', error);
    }
    
    // Fallback to offline page
    const cache = await caches.open(STATIC_CACHE);
    const offlineResponse = await cache.match('/offline.html');
    
    if (offlineResponse) {
        return offlineResponse;
    }
    
    // Return basic offline content
    return new Response(`
        <!DOCTYPE html>
        <html>
        <head>
            <title>MINGUS - Offline</title>
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                body { font-family: Arial, sans-serif; text-align: center; padding: 2rem; }
                .offline-message { background: #f0f0f0; padding: 2rem; border-radius: 8px; }
            </style>
        </head>
        <body>
            <div class="offline-message">
                <h1>📱 MINGUS</h1>
                <p>You're currently offline. Core financial assessment features are still available.</p>
                <p>Check your connection and try again.</p>
            </div>
        </body>
        </html>
    `, {
        headers: { 'Content-Type': 'text/html' }
    });
}

// Handle static resource requests
async function handleStaticRequest(request) {
    const cache = await caches.open(STATIC_CACHE);
    
    try {
        // Try cache first for static resources
        const cachedResponse = await cache.match(request);
        
        if (cachedResponse) {
            return cachedResponse;
        }
        
        // Fetch from network if not cached
        const networkResponse = await fetch(request);
        
        if (networkResponse.ok) {
            cache.put(request, networkResponse.clone());
            return networkResponse;
        }
    } catch (error) {
        console.log('Static resource fetch failed:', error);
    }
    
    return new Response('Resource not available offline', { status: 404 });
}

// Background sync for offline data
self.addEventListener('sync', (event) => {
    if (event.tag === 'sync-offline-data') {
        event.waitUntil(syncOfflineData());
    }
});

// Push notification handling
self.addEventListener('push', (event) => {
    const options = {
        body: event.data ? event.data.text() : 'New financial insights available!',
        icon: '/images/logo-192.png',
        badge: '/images/badge-72.png',
        vibrate: [100, 50, 100],
        data: {
            dateOfArrival: Date.now(),
            primaryKey: 1
        },
        actions: [
            {
                action: 'explore',
                title: 'Explore',
                icon: '/images/explore.png'
            },
            {
                action: 'close',
                title: 'Close',
                icon: '/images/close.png'
            }
        ]
    };
    
    event.waitUntil(
        self.registration.showNotification('MINGUS Financial', options)
    );
});

// Notification click handling
self.addEventListener('notificationclick', (event) => {
    event.notification.close();
    
    if (event.action === 'explore') {
        event.waitUntil(
            clients.openWindow('/')
        );
    }
});

// Utility functions
async function getNetworkInfo() {
    // Try to get network information from clients
    const clients = await self.clients.matchAll();
    
    for (const client of clients) {
        try {
            const networkInfo = await client.postMessage({
                type: 'get-network-info'
            });
            if (networkInfo) {
                return networkInfo;
            }
        } catch (error) {
            // Ignore errors
        }
    }
    
    // Default to 4G if network info unavailable
    return { effectiveType: '4g', downlink: 10 };
}

function storeOfflineData(key, data) {
    // Store data in IndexedDB for offline use
    if ('indexedDB' in self) {
        const request = indexedDB.open('MingusOfflineData', 1);
        
        request.onupgradeneeded = (event) => {
            const db = event.target.result;
            if (!db.objectStoreNames.contains('financialData')) {
                db.createObjectStore('financialData', { keyPath: 'key' });
            }
        };
        
        request.onsuccess = (event) => {
            const db = event.target.result;
            const transaction = db.transaction(['financialData'], 'readwrite');
            const store = transaction.objectStore('financialData');
            
            store.put({
                key: key,
                data: data,
                timestamp: Date.now()
            });
        };
    }
}

function getMockApiData(pathname) {
    // Return mock data for offline functionality
    const mockData = {
        '/api/salary-data': {
            industries: {
                technology: { entry: 65000, mid: 95000, senior: 140000 },
                healthcare: { entry: 55000, mid: 85000, senior: 120000 },
                finance: { entry: 60000, mid: 90000, senior: 130000 }
            }
        },
        '/api/industry-data': {
            growth: {
                technology: 15.2,
                healthcare: 8.7,
                finance: 6.3
            }
        },
        '/api/tax-brackets': {
            single: [
                { rate: 0.10, min: 0, max: 11600 },
                { rate: 0.12, min: 11601, max: 47150 }
            ]
        },
        '/api/cost-of-living': {
            'new-york': 1.5,
            'atlanta': 1.1,
            'houston': 1.0
        },
        '/api/equity-factors': {
            bias_adjustment: 0.88,
            network_access: 0.80,
            mentorship: 0.75
        }
    };
    
    return mockData[pathname] || { error: 'Data not available offline' };
}

async function syncOfflineData() {
    // Sync any stored offline data when connection is restored
    if ('indexedDB' in self) {
        const request = indexedDB.open('MingusOfflineData', 1);
        
        request.onsuccess = (event) => {
            const db = event.target.result;
            const transaction = db.transaction(['financialData'], 'readonly');
            const store = transaction.objectStore('financialData');
            const getAllRequest = store.getAll();
            
            getAllRequest.onsuccess = () => {
                const offlineData = getAllRequest.result;
                
                // Send offline data to server
                offlineData.forEach(item => {
                    fetch('/api/sync-offline-data', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            key: item.key,
                            data: item.data,
                            timestamp: item.timestamp
                        })
                    }).then(response => {
                        if (response.ok) {
                            // Remove synced data from IndexedDB
                            const deleteTransaction = db.transaction(['financialData'], 'readwrite');
                            const deleteStore = deleteTransaction.objectStore('financialData');
                            deleteStore.delete(item.key);
                        }
                    }).catch(error => {
                        console.error('Failed to sync offline data:', error);
                    });
                });
            };
        };
    }
}

// Cache management
async function manageCacheSize() {
    const cacheNames = [STATIC_CACHE, DATA_CACHE, OFFLINE_CACHE];
    
    for (const cacheName of cacheNames) {
        const cache = await caches.open(cacheName);
        const keys = await cache.keys();
        
        if (keys.length > 100) { // Limit cache entries
            const oldestKeys = keys.slice(0, 20); // Remove oldest 20 entries
            await Promise.all(oldestKeys.map(key => cache.delete(key)));
        }
    }
}

// Periodic cache cleanup
setInterval(manageCacheSize, 24 * 60 * 60 * 1000); // Daily cleanup

// Handle errors
self.addEventListener('error', (error) => {
    console.error('Service Worker error:', error);
});

self.addEventListener('unhandledrejection', (event) => {
    console.error('Service Worker unhandled rejection:', event.reason);
});
