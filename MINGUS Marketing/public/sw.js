// Service Worker for Ratchet Money - Production Optimized
const CACHE_NAME = 'ratchet-money-v1.0.0'
const STATIC_CACHE = 'ratchet-money-static-v1.0.0'
const DYNAMIC_CACHE = 'ratchet-money-dynamic-v1.0.0'
const API_CACHE = 'ratchet-money-api-v1.0.0'

// Files to cache immediately
const STATIC_FILES = [
  '/',
  '/index.html',
  '/static/js/bundle.js',
  '/static/css/main.css',
  '/manifest.json',
  '/favicon.ico',
  '/logo192.png',
  '/logo512.png',
  '/offline.html'
]

// API endpoints to cache
const API_ENDPOINTS = [
  '/api/questions',
  '/api/assessment',
  '/api/results'
]

// Install event - cache static files
self.addEventListener('install', (event) => {
  console.log('Service Worker: Installing...')
  
  event.waitUntil(
    caches.open(STATIC_CACHE)
      .then((cache) => {
        console.log('Service Worker: Caching static files')
        return cache.addAll(STATIC_FILES)
      })
      .then(() => {
        console.log('Service Worker: Static files cached')
        return self.skipWaiting()
      })
      .catch((error) => {
        console.error('Service Worker: Error caching static files', error)
      })
  )
})

// Activate event - clean up old caches
self.addEventListener('activate', (event) => {
  console.log('Service Worker: Activating...')
  
  event.waitUntil(
    caches.keys()
      .then((cacheNames) => {
        return Promise.all(
          cacheNames.map((cacheName) => {
            if (cacheName !== STATIC_CACHE && 
                cacheName !== DYNAMIC_CACHE && 
                cacheName !== API_CACHE) {
              console.log('Service Worker: Deleting old cache', cacheName)
              return caches.delete(cacheName)
            }
          })
        )
      })
      .then(() => {
        console.log('Service Worker: Activated')
        return self.clients.claim()
      })
  )
})

// Fetch event - handle requests
self.addEventListener('fetch', (event) => {
  const { request } = event
  const url = new URL(request.url)

  // Skip non-GET requests
  if (request.method !== 'GET') {
    return
  }

  // Handle different types of requests
  if (url.pathname === '/') {
    // Homepage - cache first, then network
    event.respondWith(cacheFirst(request, STATIC_CACHE))
  } else if (url.pathname.startsWith('/static/')) {
    // Static assets - cache first, then network
    event.respondWith(cacheFirst(request, STATIC_CACHE))
  } else if (url.pathname.startsWith('/api/')) {
    // API requests - network first, then cache
    event.respondWith(networkFirst(request, API_CACHE))
  } else if (url.pathname.startsWith('/images/')) {
    // Images - stale while revalidate
    event.respondWith(staleWhileRevalidate(request, DYNAMIC_CACHE))
  } else {
    // Other requests - network first, then cache
    event.respondWith(networkFirst(request, DYNAMIC_CACHE))
  }
})

// Cache First Strategy
async function cacheFirst(request, cacheName) {
  try {
    const cachedResponse = await caches.match(request)
    if (cachedResponse) {
      return cachedResponse
    }
    
    const networkResponse = await fetch(request)
    if (networkResponse.ok) {
      const cache = await caches.open(cacheName)
      cache.put(request, networkResponse.clone())
    }
    return networkResponse
  } catch (error) {
    console.error('Cache First Strategy Error:', error)
    return new Response('Network error', { status: 503 })
  }
}

// Network First Strategy
async function networkFirst(request, cacheName) {
  try {
    const networkResponse = await fetch(request)
    if (networkResponse.ok) {
      const cache = await caches.open(cacheName)
      cache.put(request, networkResponse.clone())
    }
    return networkResponse
  } catch (error) {
    console.log('Network failed, trying cache:', error)
    const cachedResponse = await caches.match(request)
    if (cachedResponse) {
      return cachedResponse
    }
    
    // Return offline page for HTML requests
    if (request.headers.get('accept').includes('text/html')) {
      return caches.match('/offline.html')
    }
    
    return new Response('Offline', { status: 503 })
  }
}

// Stale While Revalidate Strategy
async function staleWhileRevalidate(request, cacheName) {
  const cache = await caches.open(cacheName)
  const cachedResponse = await cache.match(request)
  
  const fetchPromise = fetch(request).then((networkResponse) => {
    if (networkResponse.ok) {
      cache.put(request, networkResponse.clone())
    }
    return networkResponse
  }).catch(() => {
    // Network failed, return cached response if available
    return cachedResponse || new Response('Image not available', { status: 404 })
  })
  
  return cachedResponse || fetchPromise
}

// Background Sync for offline form submissions
self.addEventListener('sync', (event) => {
  if (event.tag === 'background-sync') {
    console.log('Service Worker: Background sync triggered')
    event.waitUntil(doBackgroundSync())
  }
})

async function doBackgroundSync() {
  try {
    // Get pending requests from IndexedDB
    const pendingRequests = await getPendingRequests()
    
    for (const request of pendingRequests) {
      try {
        const response = await fetch(request.url, {
          method: request.method,
          headers: request.headers,
          body: request.body
        })
        
        if (response.ok) {
          // Remove from pending requests
          await removePendingRequest(request.id)
          console.log('Background sync: Request completed', request.id)
        }
      } catch (error) {
        console.error('Background sync: Request failed', request.id, error)
      }
    }
  } catch (error) {
    console.error('Background sync error:', error)
  }
}

// Push notifications
self.addEventListener('push', (event) => {
  console.log('Service Worker: Push received')
  
  const options = {
    body: event.data ? event.data.text() : 'New update available!',
    icon: '/logo192.png',
    badge: '/logo192.png',
    vibrate: [100, 50, 100],
    data: {
      dateOfArrival: Date.now(),
      primaryKey: 1
    },
    actions: [
      {
        action: 'explore',
        title: 'View Assessment',
        icon: '/logo192.png'
      },
      {
        action: 'close',
        title: 'Close',
        icon: '/logo192.png'
      }
    ]
  }
  
  event.waitUntil(
    self.registration.showNotification('Ratchet Money', options)
  )
})

// Notification click
self.addEventListener('notificationclick', (event) => {
  console.log('Service Worker: Notification clicked')
  
  event.notification.close()
  
  if (event.action === 'explore') {
    event.waitUntil(
      clients.openWindow('/')
    )
  }
})

// IndexedDB helpers for background sync
async function getPendingRequests() {
  // Implementation for getting pending requests from IndexedDB
  return []
}

async function removePendingRequest(id) {
  // Implementation for removing completed requests from IndexedDB
}

// Performance monitoring
self.addEventListener('message', (event) => {
  if (event.data && event.data.type === 'SKIP_WAITING') {
    self.skipWaiting()
  }
  
  if (event.data && event.data.type === 'GET_VERSION') {
    event.ports[0].postMessage({ version: CACHE_NAME })
  }
})

// Error handling
self.addEventListener('error', (event) => {
  console.error('Service Worker Error:', event.error)
})

self.addEventListener('unhandledrejection', (event) => {
  console.error('Service Worker Unhandled Rejection:', event.reason)
})

// Cache cleanup - run periodically
async function cleanupOldCaches() {
  try {
    const cacheNames = await caches.keys()
    const currentCaches = [STATIC_CACHE, DYNAMIC_CACHE, API_CACHE]
    
    for (const cacheName of cacheNames) {
      if (!currentCaches.includes(cacheName)) {
        await caches.delete(cacheName)
        console.log('Service Worker: Cleaned up old cache', cacheName)
      }
    }
  } catch (error) {
    console.error('Service Worker: Cache cleanup error', error)
  }
}

// Run cleanup every 24 hours
setInterval(cleanupOldCaches, 24 * 60 * 60 * 1000) 