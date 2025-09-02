/**
 * Service Worker for AI Job Impact Calculator
 * Provides offline support, caching, and background sync
 */

const CACHE_NAME = 'ai-calculator-v1.0.0';
const STATIC_CACHE = 'ai-calculator-static-v1.0.0';
const DYNAMIC_CACHE = 'ai-calculator-dynamic-v1.0.0';

// Cache strategies
const CACHE_STRATEGIES = {
    STATIC: 'cache-first',
    DYNAMIC: 'network-first',
    API: 'network-first',
    IMAGES: 'cache-first'
};

// Files to cache immediately
const STATIC_FILES = [
    '/',
    '/ai-job-impact-calculator.html',
    '/static/css/main.min.css',
    '/static/css/calculator.min.css',
    '/static/js/calculator-optimized.js',
    '/static/images/logo.webp',
    '/static/images/hero.webp',
    '/static/images/icons.svg',
    '/manifest.json'
];

// API endpoints to cache
const API_ENDPOINTS = [
    '/api/ai-job-assessment',
    '/api/job-risk-data',
    '/api/analytics/performance'
];

// Install event - cache static files
self.addEventListener('install', (event) => {
    console.log('Service Worker installing...');
    
    event.waitUntil(
        caches.open(STATIC_CACHE)
            .then((cache) => {
                console.log('Caching static files');
                return cache.addAll(STATIC_FILES);
            })
            .then(() => {
                console.log('Static files cached successfully');
                return self.skipWaiting();
            })
            .catch((error) => {
                console.error('Failed to cache static files:', error);
            })
    );
});

// Activate event - clean up old caches
self.addEventListener('activate', (event) => {
    console.log('Service Worker activating...');
    
    event.waitUntil(
        caches.keys()
            .then((cacheNames) => {
                return Promise.all(
                    cacheNames.map((cacheName) => {
                        if (cacheName !== STATIC_CACHE && cacheName !== DYNAMIC_CACHE) {
                            console.log('Deleting old cache:', cacheName);
                            return caches.delete(cacheName);
                        }
                    })
                );
            })
            .then(() => {
                console.log('Service Worker activated');
                return self.clients.claim();
            })
    );
});

// Fetch event - handle requests
self.addEventListener('fetch', (event) => {
    const { request } = event;
    const url = new URL(request.url);
    
    // Skip non-GET requests
    if (request.method !== 'GET') {
        return;
    }
    
    // Handle different types of requests
    if (isStaticFile(url.pathname)) {
        event.respondWith(handleStaticFile(request));
    } else if (isAPIRequest(url.pathname)) {
        event.respondWith(handleAPIRequest(request));
    } else if (isImageRequest(url.pathname)) {
        event.respondWith(handleImageRequest(request));
    } else {
        event.respondWith(handleDynamicRequest(request));
    }
});

// Background sync for offline submissions
self.addEventListener('sync', (event) => {
    if (event.tag === 'offline-assessment-sync') {
        console.log('Background sync triggered');
        event.waitUntil(syncOfflineAssessments());
    }
});

// Push notifications (if enabled)
self.addEventListener('push', (event) => {
    if (event.data) {
        const data = event.data.json();
        const options = {
            body: data.body,
            icon: '/static/images/logo.webp',
            badge: '/static/images/badge.webp',
            data: data.data,
            actions: data.actions || []
        };
        
        event.waitUntil(
            self.registration.showNotification(data.title, options)
        );
    }
});

// Notification click handler
self.addEventListener('notificationclick', (event) => {
    event.notification.close();
    
    if (event.action) {
        // Handle specific actions
        handleNotificationAction(event.action, event.notification.data);
    } else {
        // Default action - open calculator
        event.waitUntil(
            clients.openWindow('/ai-job-impact-calculator.html')
        );
    }
});

// Helper functions
function isStaticFile(pathname) {
    return STATIC_FILES.some(file => pathname === file || pathname.startsWith('/static/'));
}

function isAPIRequest(pathname) {
    return API_ENDPOINTS.some(endpoint => pathname.startsWith(endpoint));
}

function isImageRequest(pathname) {
    return /\.(jpg|jpeg|png|gif|webp|svg)$/i.test(pathname);
}

// Cache strategies
async function handleStaticFile(request) {
    try {
        const cache = await caches.open(STATIC_CACHE);
        const cachedResponse = await cache.match(request);
        
        if (cachedResponse) {
            return cachedResponse;
        }
        
        const networkResponse = await fetch(request);
        if (networkResponse.ok) {
            cache.put(request, networkResponse.clone());
        }
        
        return networkResponse;
    } catch (error) {
        console.error('Static file fetch failed:', error);
        return new Response('Offline - Static file not available', { status: 503 });
    }
}

async function handleAPIRequest(request) {
    try {
        // Try network first
        const networkResponse = await fetch(request);
        
        if (networkResponse.ok) {
            // Cache successful API responses
            const cache = await caches.open(DYNAMIC_CACHE);
            cache.put(request, networkResponse.clone());
        }
        
        return networkResponse;
    } catch (error) {
        console.log('API request failed, trying cache:', error);
        
        // Fallback to cache
        const cache = await caches.open(DYNAMIC_CACHE);
        const cachedResponse = await cache.match(request);
        
        if (cachedResponse) {
            return cachedResponse;
        }
        
        // Return offline response for API requests
        return new Response(JSON.stringify({
            error: 'Offline - Please check your connection and try again',
            offline: true
        }), {
            status: 503,
            headers: { 'Content-Type': 'application/json' }
        });
    }
}

async function handleImageRequest(request) {
    try {
        const cache = await caches.open(DYNAMIC_CACHE);
        const cachedResponse = await cache.match(request);
        
        if (cachedResponse) {
            return cachedResponse;
        }
        
        const networkResponse = await fetch(request);
        if (networkResponse.ok) {
            cache.put(request, networkResponse.clone());
        }
        
        return networkResponse;
    } catch (error) {
        console.error('Image fetch failed:', error);
        return new Response('Image not available offline', { status: 503 });
    }
}

async function handleDynamicRequest(request) {
    try {
        // Try network first for dynamic content
        const networkResponse = await fetch(request);
        
        if (networkResponse.ok) {
            // Cache successful responses
            const cache = await caches.open(DYNAMIC_CACHE);
            cache.put(request, networkResponse.clone());
        }
        
        return networkResponse;
    } catch (error) {
        console.log('Dynamic request failed, trying cache:', error);
        
        // Fallback to cache
        const cache = await caches.open(DYNAMIC_CACHE);
        const cachedResponse = await cache.match(request);
        
        if (cachedResponse) {
            return cachedResponse;
        }
        
        // Return offline page
        return caches.match('/offline.html');
    }
}

// Background sync for offline assessments
async function syncOfflineAssessments() {
    try {
        // Get offline assessments from IndexedDB or localStorage
        const offlineAssessments = await getOfflineAssessments();
        
        if (offlineAssessments.length === 0) {
            console.log('No offline assessments to sync');
            return;
        }
        
        console.log(`Syncing ${offlineAssessments.length} offline assessments`);
        
        for (const assessment of offlineAssessments) {
            try {
                const response = await fetch('/api/ai-job-assessment', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(assessment.data)
                });
                
                if (response.ok) {
                    // Remove from offline storage
                    await removeOfflineAssessment(assessment.id);
                    console.log('Successfully synced assessment:', assessment.id);
                } else {
                    console.error('Failed to sync assessment:', assessment.id);
                }
            } catch (error) {
                console.error('Error syncing assessment:', assessment.id, error);
            }
        }
    } catch (error) {
        console.error('Background sync failed:', error);
    }
}

// IndexedDB operations for offline storage
async function getOfflineAssessments() {
    return new Promise((resolve) => {
        const request = indexedDB.open('ai-calculator-offline', 1);
        
        request.onerror = () => resolve([]);
        
        request.onsuccess = (event) => {
            const db = event.target.result;
            const transaction = db.transaction(['assessments'], 'readonly');
            const store = transaction.objectStore('assessments');
            const getAllRequest = store.getAll();
            
            getAllRequest.onsuccess = () => resolve(getAllRequest.result || []);
            getAllRequest.onerror = () => resolve([]);
        };
        
        request.onupgradeneeded = (event) => {
            const db = event.target.result;
            if (!db.objectStoreNames.contains('assessments')) {
                db.createObjectStore('assessments', { keyPath: 'id' });
            }
        };
    });
}

async function removeOfflineAssessment(id) {
    return new Promise((resolve) => {
        const request = indexedDB.open('ai-calculator-offline', 1);
        
        request.onerror = () => resolve(false);
        
        request.onsuccess = (event) => {
            const db = event.target.result;
            const transaction = db.transaction(['assessments'], 'readwrite');
            const store = transaction.objectStore('assessments');
            const deleteRequest = store.delete(id);
            
            deleteRequest.onsuccess = () => resolve(true);
            deleteRequest.onerror = () => resolve(false);
        };
    });
}

// Notification action handlers
function handleNotificationAction(action, data) {
    switch (action) {
        case 'view_results':
            clients.openWindow(`/ai-job-impact-calculator.html?assessment=${data.assessmentId}`);
            break;
        case 'retake_assessment':
            clients.openWindow('/ai-job-impact-calculator.html');
            break;
        default:
            clients.openWindow('/ai-job-impact-calculator.html');
    }
}

// Cache cleanup
async function cleanupOldCaches() {
    try {
        const cacheNames = await caches.keys();
        const currentCaches = [STATIC_CACHE, DYNAMIC_CACHE];
        
        for (const cacheName of cacheNames) {
            if (!currentCaches.includes(cacheName)) {
                await caches.delete(cacheName);
                console.log('Deleted old cache:', cacheName);
            }
        }
    } catch (error) {
        console.error('Cache cleanup failed:', error);
    }
}

// Periodic cache cleanup
setInterval(cleanupOldCaches, 24 * 60 * 60 * 1000); // Daily cleanup

console.log('Service Worker loaded successfully');
