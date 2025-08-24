const CACHE_NAME = 'mingus-income-v1';
const STATIC_CACHE = 'mingus-static-v1';
const DATA_CACHE = 'mingus-data-v1';

// Files to cache for offline functionality
const STATIC_FILES = [
  '/',
  '/index.html',
  '/static/js/bundle.js',
  '/static/css/main.css',
  '/manifest.json',
  '/offline.html'
];

// API endpoints to cache for offline data
const API_CACHE_PATTERNS = [
  '/api/salary-data',
  '/api/career-paths',
  '/api/cultural-context',
  '/api/benchmark-data'
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
        console.error('Error caching static files:', error);
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
            if (cacheName !== STATIC_CACHE && cacheName !== DATA_CACHE) {
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

// Fetch event - serve from cache when offline
self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);

  // Handle API requests for salary data
  if (API_CACHE_PATTERNS.some(pattern => url.pathname.includes(pattern))) {
    event.respondWith(handleApiRequest(request));
    return;
  }

  // Handle static file requests
  if (request.method === 'GET' && request.destination !== 'document') {
    event.respondWith(handleStaticRequest(request));
    return;
  }

  // Handle navigation requests
  if (request.mode === 'navigate') {
    event.respondWith(handleNavigationRequest(request));
    return;
  }
});

// Handle API requests with offline fallback
async function handleApiRequest(request) {
  try {
    // Try to fetch from network first
    const networkResponse = await fetch(request);
    
    if (networkResponse.ok) {
      // Cache the successful response
      const cache = await caches.open(DATA_CACHE);
      cache.put(request, networkResponse.clone());
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

  // Return mock data if no cache available
  return new Response(JSON.stringify(getMockData(request.url)), {
    headers: { 'Content-Type': 'application/json' }
  });
}

// Handle static file requests
async function handleStaticRequest(request) {
  const cache = await caches.open(STATIC_CACHE);
  const cachedResponse = await cache.match(request);
  
  if (cachedResponse) {
    return cachedResponse;
  }

  try {
    const networkResponse = await fetch(request);
    if (networkResponse.ok) {
      cache.put(request, networkResponse.clone());
    }
    return networkResponse;
  } catch (error) {
    console.log('Static file fetch failed:', error);
    return new Response('', { status: 404 });
  }
}

// Handle navigation requests
async function handleNavigationRequest(request) {
  try {
    const networkResponse = await fetch(request);
    return networkResponse;
  } catch (error) {
    console.log('Navigation failed, serving offline page:', error);
    const cache = await caches.open(STATIC_CACHE);
    const offlineResponse = await cache.match('/offline.html');
    return offlineResponse || new Response('Offline - Please check your connection');
  }
}

// Mock data for offline functionality
function getMockData(url) {
  if (url.includes('salary-data')) {
    return {
      userSalary: 75000,
      peerAverage: 82000,
      peerMedian: 78000,
      peer75thPercentile: 95000,
      peer25thPercentile: 65000,
      confidenceInterval: { lower: 76000, upper: 88000 },
      sampleSize: 1247,
      msa: 'Atlanta-Sandy Springs-Alpharetta, GA',
      industry: 'Technology',
      experienceLevel: 'Mid-Level (3-7 years)',
      educationLevel: 'Bachelor\'s Degree'
    };
  }

  if (url.includes('career-paths')) {
    return {
      currentSalary: 75000,
      targetSalary: 100000,
      yearsToTarget: 2,
      steps: [
        {
          id: 'education',
          title: 'Pursue Advanced Degree',
          description: 'Complete Master\'s in Computer Science or MBA',
          cost: 45000,
          duration: 24,
          salaryIncrease: 15000,
          type: 'education',
          priority: 'high'
        }
      ],
      totalInvestment: 52000,
      roi: 144
    };
  }

  if (url.includes('cultural-context')) {
    return {
      representationPremium: 8500,
      salaryGap: 12000,
      systemicBarriers: [
        'Unconscious bias in hiring and promotion processes',
        'Limited access to high-profile projects and mentorship'
      ],
      diverseLeadershipBonus: 15000,
      communityWealthBuilding: {
        mentorshipOpportunities: 85,
        networkingGroups: 23,
        investmentOpportunities: 12
      }
    };
  }

  return {};
}

// Background sync for data updates
self.addEventListener('sync', (event) => {
  if (event.tag === 'background-sync') {
    event.waitUntil(syncData());
  }
});

// Sync data when connection is restored
async function syncData() {
  try {
    const cache = await caches.open(DATA_CACHE);
    const requests = await cache.keys();
    
    for (const request of requests) {
      try {
        const response = await fetch(request);
        if (response.ok) {
          cache.put(request, response);
        }
      } catch (error) {
        console.log('Failed to sync request:', request.url, error);
      }
    }
  } catch (error) {
    console.log('Background sync failed:', error);
  }
}

// Push notification handling
self.addEventListener('push', (event) => {
  const options = {
    body: event.data ? event.data.text() : 'New salary insights available!',
    icon: '/icons/icon-192x192.png',
    badge: '/icons/badge-72x72.png',
    vibrate: [100, 50, 100],
    data: {
      dateOfArrival: Date.now(),
      primaryKey: 1
    },
    actions: [
      {
        action: 'explore',
        title: 'View Insights',
        icon: '/icons/action-1.png'
      },
      {
        action: 'close',
        title: 'Close',
        icon: '/icons/action-2.png'
      }
    ]
  };

  event.waitUntil(
    self.registration.showNotification('Mingus Income Dashboard', options)
  );
});

// Notification click handling
self.addEventListener('notificationclick', (event) => {
  event.notification.close();

  if (event.action === 'explore') {
    event.waitUntil(
      clients.openWindow('/?tab=benchmark')
    );
  }
}); 