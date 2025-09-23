/**
 * Mingus Application - Service Worker
 * Offline support and caching for Daily Outlook system
 */

const CACHE_NAME = 'mingus-daily-outlook-v1';
const STATIC_CACHE_NAME = 'mingus-static-v1';
const API_CACHE_NAME = 'mingus-api-v1';

// Cache strategies
const CACHE_STRATEGIES = {
  // Static assets - cache first
  STATIC: {
    pattern: /\.(js|css|png|jpg|jpeg|gif|svg|webp|woff|woff2|ttf|eot)$/,
    strategy: 'cache-first',
    ttl: 7 * 24 * 60 * 60 * 1000 // 7 days
  },
  
  // API endpoints - network first with fallback
  API: {
    pattern: /^\/api\//,
    strategy: 'network-first',
    ttl: 60 * 60 * 1000 // 1 hour
  },
  
  // Daily Outlook specific - cache first with background sync
  DAILY_OUTLOOK: {
    pattern: /\/api\/daily-outlook/,
    strategy: 'cache-first',
    ttl: 24 * 60 * 60 * 1000 // 24 hours
  },
  
  // User data - network first with short cache
  USER_DATA: {
    pattern: /\/api\/user\//,
    strategy: 'network-first',
    ttl: 5 * 60 * 1000 // 5 minutes
  }
};

// Critical resources to cache immediately
const CRITICAL_RESOURCES = [
  '/',
  '/static/css/main.css',
  '/static/js/main.js',
  '/static/images/logo.png',
  '/static/images/daily-outlook-bg.webp',
  '/manifest.json'
];

// Install event - cache critical resources
self.addEventListener('install', event => {
  console.log('Service Worker installing...');
  
  event.waitUntil(
    caches.open(STATIC_CACHE_NAME)
      .then(cache => {
        console.log('Caching critical resources...');
        return cache.addAll(CRITICAL_RESOURCES);
      })
      .then(() => {
        console.log('Critical resources cached successfully');
        return self.skipWaiting();
      })
      .catch(error => {
        console.error('Failed to cache critical resources:', error);
      })
  );
});

// Activate event - clean up old caches
self.addEventListener('activate', event => {
  console.log('Service Worker activating...');
  
  event.waitUntil(
    caches.keys()
      .then(cacheNames => {
        return Promise.all(
          cacheNames.map(cacheName => {
            if (cacheName !== CACHE_NAME && 
                cacheName !== STATIC_CACHE_NAME && 
                cacheName !== API_CACHE_NAME) {
              console.log('Deleting old cache:', cacheName);
              return caches.delete(cacheName);
            }
          })
        );
      })
      .then(() => {
        console.log('Service Worker activated successfully');
        return self.clients.claim();
      })
  );
});

// Fetch event - implement caching strategies
self.addEventListener('fetch', event => {
  const { request } = event;
  const url = new URL(request.url);
  
  // Skip non-GET requests
  if (request.method !== 'GET') {
    return;
  }
  
  // Skip chrome-extension and other non-http requests
  if (!url.protocol.startsWith('http')) {
    return;
  }
  
  // Determine cache strategy based on URL pattern
  const strategy = getCacheStrategy(url.pathname);
  
  if (strategy) {
    event.respondWith(handleRequest(request, strategy));
  }
});

// Get cache strategy for URL
function getCacheStrategy(pathname) {
  for (const [name, config] of Object.entries(CACHE_STRATEGIES)) {
    if (config.pattern.test(pathname)) {
      return { ...config, name };
    }
  }
  return null;
}

// Handle request based on strategy
async function handleRequest(request, strategy) {
  const cache = await caches.open(getCacheName(strategy.name));
  
  switch (strategy.strategy) {
    case 'cache-first':
      return cacheFirst(request, cache, strategy);
    
    case 'network-first':
      return networkFirst(request, cache, strategy);
    
    case 'network-only':
      return networkOnly(request);
    
    case 'cache-only':
      return cacheOnly(request, cache);
    
    default:
      return fetch(request);
  }
}

// Cache first strategy
async function cacheFirst(request, cache, strategy) {
  try {
    // Try cache first
    const cachedResponse = await cache.match(request);
    if (cachedResponse && !isExpired(cachedResponse, strategy.ttl)) {
      console.log('Cache hit:', request.url);
      return cachedResponse;
    }
    
    // If not in cache or expired, fetch from network
    const networkResponse = await fetch(request);
    
    if (networkResponse.ok) {
      // Cache the response
      const responseToCache = networkResponse.clone();
      await cache.put(request, responseToCache);
      console.log('Cached response:', request.url);
    }
    
    return networkResponse;
    
  } catch (error) {
    console.error('Cache-first strategy failed:', error);
    
    // Fallback to cache even if expired
    const cachedResponse = await cache.match(request);
    if (cachedResponse) {
      console.log('Using expired cache as fallback:', request.url);
      return cachedResponse;
    }
    
    // Return offline page for navigation requests
    if (request.mode === 'navigate') {
      return caches.match('/offline.html');
    }
    
    throw error;
  }
}

// Network first strategy
async function networkFirst(request, cache, strategy) {
  try {
    // Try network first
    const networkResponse = await fetch(request);
    
    if (networkResponse.ok) {
      // Cache the response
      const responseToCache = networkResponse.clone();
      await cache.put(request, responseToCache);
      console.log('Network response cached:', request.url);
    }
    
    return networkResponse;
    
  } catch (error) {
    console.log('Network failed, trying cache:', request.url);
    
    // Fallback to cache
    const cachedResponse = await cache.match(request);
    if (cachedResponse && !isExpired(cachedResponse, strategy.ttl)) {
      console.log('Cache fallback hit:', request.url);
      return cachedResponse;
    }
    
    // Return offline page for navigation requests
    if (request.mode === 'navigate') {
      return caches.match('/offline.html');
    }
    
    throw error;
  }
}

// Network only strategy
async function networkOnly(request) {
  return fetch(request);
}

// Cache only strategy
async function cacheOnly(request, cache) {
  const cachedResponse = await cache.match(request);
  if (cachedResponse) {
    return cachedResponse;
  }
  
  throw new Error('No cached response available');
}

// Get cache name based on strategy
function getCacheName(strategyName) {
  switch (strategyName) {
    case 'STATIC':
      return STATIC_CACHE_NAME;
    case 'API':
    case 'DAILY_OUTLOOK':
    case 'USER_DATA':
      return API_CACHE_NAME;
    default:
      return CACHE_NAME;
  }
}

// Check if cached response is expired
function isExpired(response, ttl) {
  const cacheDate = response.headers.get('sw-cache-date');
  if (!cacheDate) {
    return false; // No cache date, assume not expired
  }
  
  const cacheTime = new Date(cacheDate).getTime();
  const now = Date.now();
  return (now - cacheTime) > ttl;
}

// Background sync for offline actions
self.addEventListener('sync', event => {
  console.log('Background sync triggered:', event.tag);
  
  if (event.tag === 'daily-outlook-sync') {
    event.waitUntil(syncDailyOutlookData());
  } else if (event.tag === 'user-data-sync') {
    event.waitUntil(syncUserData());
  }
});

// Sync daily outlook data when back online
async function syncDailyOutlookData() {
  try {
    console.log('Syncing daily outlook data...');
    
    // Get pending offline actions from IndexedDB
    const pendingActions = await getPendingActions('daily-outlook');
    
    for (const action of pendingActions) {
      try {
        await fetch(action.url, {
          method: action.method,
          headers: action.headers,
          body: action.body
        });
        
        // Remove from pending actions
        await removePendingAction('daily-outlook', action.id);
        console.log('Synced daily outlook action:', action.id);
        
      } catch (error) {
        console.error('Failed to sync daily outlook action:', error);
      }
    }
    
  } catch (error) {
    console.error('Daily outlook sync failed:', error);
  }
}

// Sync user data when back online
async function syncUserData() {
  try {
    console.log('Syncing user data...');
    
    const pendingActions = await getPendingActions('user-data');
    
    for (const action of pendingActions) {
      try {
        await fetch(action.url, {
          method: action.method,
          headers: action.headers,
          body: action.body
        });
        
        await removePendingAction('user-data', action.id);
        console.log('Synced user data action:', action.id);
        
      } catch (error) {
        console.error('Failed to sync user data action:', error);
      }
    }
    
  } catch (error) {
    console.error('User data sync failed:', error);
  }
}

// IndexedDB operations for offline actions
async function getPendingActions(type) {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open('mingus-offline-actions', 1);
    
    request.onerror = () => reject(request.error);
    
    request.onsuccess = () => {
      const db = request.result;
      const transaction = db.transaction(['actions'], 'readonly');
      const store = transaction.objectStore('actions');
      const index = store.index('type');
      const getRequest = index.getAll(type);
      
      getRequest.onsuccess = () => resolve(getRequest.result);
      getRequest.onerror = () => reject(getRequest.error);
    };
    
    request.onupgradeneeded = () => {
      const db = request.result;
      if (!db.objectStoreNames.contains('actions')) {
        const store = db.createObjectStore('actions', { keyPath: 'id', autoIncrement: true });
        store.createIndex('type', 'type', { unique: false });
      }
    };
  });
}

async function removePendingAction(type, id) {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open('mingus-offline-actions', 1);
    
    request.onsuccess = () => {
      const db = request.result;
      const transaction = db.transaction(['actions'], 'readwrite');
      const store = transaction.objectStore('actions');
      const deleteRequest = store.delete(id);
      
      deleteRequest.onsuccess = () => resolve();
      deleteRequest.onerror = () => reject(deleteRequest.error);
    };
    
    request.onerror = () => reject(request.error);
  });
}

// Push notifications for Daily Outlook updates
self.addEventListener('push', event => {
  console.log('Push notification received:', event);
  
  if (event.data) {
    const data = event.data.json();
    
    const options = {
      body: data.body || 'Your daily outlook is ready!',
      icon: '/static/images/icon-192x192.png',
      badge: '/static/images/badge-72x72.png',
      tag: 'daily-outlook',
      data: data.data || {},
      actions: [
        {
          action: 'view',
          title: 'View Outlook',
          icon: '/static/images/view-icon.png'
        },
        {
          action: 'dismiss',
          title: 'Dismiss',
          icon: '/static/images/dismiss-icon.png'
        }
      ]
    };
    
    event.waitUntil(
      self.registration.showNotification(data.title || 'Daily Outlook Update', options)
    );
  }
});

// Handle notification clicks
self.addEventListener('notificationclick', event => {
  console.log('Notification clicked:', event);
  
  event.notification.close();
  
  if (event.action === 'view') {
    event.waitUntil(
      clients.openWindow('/daily-outlook')
    );
  }
});

// Message handling for cache management
self.addEventListener('message', event => {
  console.log('Service Worker message received:', event.data);
  
  if (event.data && event.data.type === 'SKIP_WAITING') {
    self.skipWaiting();
  } else if (event.data && event.data.type === 'CLEAR_CACHE') {
    event.waitUntil(clearAllCaches());
  } else if (event.data && event.data.type === 'CACHE_DAILY_OUTLOOK') {
    event.waitUntil(cacheDailyOutlookData(event.data.data));
  }
});

// Clear all caches
async function clearAllCaches() {
  const cacheNames = await caches.keys();
  await Promise.all(
    cacheNames.map(cacheName => caches.delete(cacheName))
  );
  console.log('All caches cleared');
}

// Cache daily outlook data
async function cacheDailyOutlookData(data) {
  const cache = await caches.open(API_CACHE_NAME);
  const response = new Response(JSON.stringify(data), {
    headers: {
      'Content-Type': 'application/json',
      'sw-cache-date': new Date().toISOString()
    }
  });
  
  await cache.put('/api/daily-outlook', response);
  console.log('Daily outlook data cached');
}

console.log('Service Worker loaded successfully');
