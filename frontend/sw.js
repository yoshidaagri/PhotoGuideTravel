// Service Worker for Tourism AI PWA
const CACHE_NAME = 'tourism-ai-v1.0.0';
const API_CACHE_NAME = 'tourism-api-cache-v1';

// Files to cache for offline use
const STATIC_CACHE_FILES = [
  './tourism-guide.html',
  './manifest.json',
  // Add any other static assets
];

// API endpoints to cache
const API_ENDPOINTS = [
  'https://f4n095fm2j.execute-api.ap-northeast-1.amazonaws.com/dev/analyze'
];

// Install event - cache static files
self.addEventListener('install', (event) => {
  console.log('Service Worker: Installing...');
  
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => {
        console.log('Service Worker: Caching static files');
        return cache.addAll(STATIC_CACHE_FILES);
      })
      .then(() => {
        console.log('Service Worker: Static files cached successfully');
        return self.skipWaiting();
      })
      .catch((error) => {
        console.error('Service Worker: Failed to cache static files:', error);
      })
  );
});

// Activate event - clean up old caches
self.addEventListener('activate', (event) => {
  console.log('Service Worker: Activating...');
  
  event.waitUntil(
    caches.keys()
      .then((cacheNames) => {
        return Promise.all(
          cacheNames.map((cacheName) => {
            if (cacheName !== CACHE_NAME && cacheName !== API_CACHE_NAME) {
              console.log('Service Worker: Deleting old cache:', cacheName);
              return caches.delete(cacheName);
            }
          })
        );
      })
      .then(() => {
        console.log('Service Worker: Activated');
        return self.clients.claim();
      })
  );
});

// Fetch event - handle requests with caching strategies
self.addEventListener('fetch', (event) => {
  const requestURL = new URL(event.request.url);
  
  // Handle API requests with network-first strategy
  if (API_ENDPOINTS.some(endpoint => event.request.url.includes(endpoint))) {
    event.respondWith(handleAPIRequest(event.request));
    return;
  }
  
  // Handle static files with cache-first strategy
  if (event.request.method === 'GET') {
    event.respondWith(handleStaticRequest(event.request));
    return;
  }
  
  // For other requests, just fetch from network
  event.respondWith(fetch(event.request));
});

// Network-first strategy for API requests
async function handleAPIRequest(request) {
  const cache = await caches.open(API_CACHE_NAME);
  
  try {
    // Try network first
    const networkResponse = await fetch(request);
    
    // If successful, cache the response and return it
    if (networkResponse.ok) {
      const responseClone = networkResponse.clone();
      await cache.put(request, responseClone);
      console.log('Service Worker: API response cached');
    }
    
    return networkResponse;
  } catch (error) {
    // Network failed, try cache
    console.log('Service Worker: Network failed, trying cache for API request');
    const cachedResponse = await cache.match(request);
    
    if (cachedResponse) {
      console.log('Service Worker: Serving API response from cache');
      return cachedResponse;
    }
    
    // No cache available, return offline response
    return new Response(
      JSON.stringify({
        error: 'オフライン状態です',
        analysis: '現在オフライン状態のため、画像解析を実行できません。インターネット接続を確認してから再度お試しください。\n\n観光AIは以下の情報を提供できます：\n• 各地域の詳細情報\n• 名物料理・ご当地グルメ\n• 季節ごとの観光スポット\n• 交通・アクセス情報\n• 地元おすすめの穴場スポット',
        offline: true,
        timestamp: new Date().toISOString()
      }),
      {
        status: 200,
        headers: {
          'Content-Type': 'application/json',
          'Cache-Control': 'no-cache'
        }
      }
    );
  }
}

// Cache-first strategy for static files
async function handleStaticRequest(request) {
  const cache = await caches.open(CACHE_NAME);
  const cachedResponse = await cache.match(request);
  
  if (cachedResponse) {
    console.log('Service Worker: Serving from cache:', request.url);
    return cachedResponse;
  }
  
  try {
    const networkResponse = await fetch(request);
    
    // Cache successful responses
    if (networkResponse.ok) {
      const responseClone = networkResponse.clone();
      await cache.put(request, responseClone);
      console.log('Service Worker: Cached new resource:', request.url);
    }
    
    return networkResponse;
  } catch (error) {
    console.error('Service Worker: Failed to fetch resource:', error);
    
    // Return offline page for navigation requests
    if (request.mode === 'navigate') {
      return new Response(`
        <!DOCTYPE html>
        <html lang="ja">
        <head>
          <meta charset="UTF-8">
          <meta name="viewport" content="width=device-width, initial-scale=1.0">
          <title>オフライン - 観光AI</title>
          <style>
            body { font-family: -apple-system, BlinkMacSystemFont, sans-serif; text-align: center; padding: 2rem; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; min-height: 100vh; display: flex; flex-direction: column; justify-content: center; }
            .offline-card { background: rgba(255,255,255,0.95); color: #333; padding: 2rem; border-radius: 20px; max-width: 400px; margin: 0 auto; }
            .offline-icon { font-size: 4rem; margin-bottom: 1rem; }
            h1 { color: #2196F3; margin-bottom: 1rem; }
            p { line-height: 1.6; margin-bottom: 1rem; }
            button { background: #2196F3; color: white; border: none; padding: 1rem 2rem; border-radius: 10px; cursor: pointer; font-size: 1rem; }
            button:hover { background: #1976D2; }
          </style>
        </head>
        <body>
          <div class="offline-card">
            <div class="offline-icon">🏔️</div>
            <h1>観光AI</h1>
            <p><strong>オフライン状態です</strong></p>
            <p>インターネット接続を確認してから再度お試しください。</p>
            <button onclick="window.location.reload()">🔄 再読み込み</button>
          </div>
        </body>
        </html>
      `, {
        status: 200,
        headers: { 'Content-Type': 'text/html' }
      });
    }
    
    return new Response('Network error occurred', { status: 408 });
  }
}

// Background sync for offline actions
self.addEventListener('sync', (event) => {
  console.log('Service Worker: Background sync triggered:', event.tag);
  
  if (event.tag === 'offline-analysis') {
    event.waitUntil(processOfflineAnalysis());
  }
});

// Push notification handling
self.addEventListener('push', (event) => {
  console.log('Service Worker: Push notification received');
  
  const options = {
    body: '新しい観光情報が利用可能です',
    icon: 'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 96 96"><rect width="96" height="96" fill="%232196F3" rx="16"/><text x="48" y="60" font-size="40" text-anchor="middle" fill="white">🏔️</text></svg>',
    badge: 'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><rect width="24" height="24" fill="%232196F3" rx="4"/><text x="12" y="16" font-size="12" text-anchor="middle" fill="white">🏔️</text></svg>',
    tag: 'tourism-update',
    actions: [
      {
        action: 'open',
        title: '開く',
        icon: 'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path fill="white" d="M19 19H5V5h7V3H5c-1.11 0-2 .9-2 2v14c0 1.1.89 2 2 2h14c1.1 0 2-.9 2-2v-7h-2v7z"/><path fill="white" d="M14 3v2h3.59l-9.83 9.83 1.41 1.41L19 6.41V10h2V3h-7z"/></svg>'
      }
    ]
  };
  
  event.waitUntil(
    self.registration.showNotification('観光AI', options)
  );
});

// Notification click handling
self.addEventListener('notificationclick', (event) => {
  console.log('Service Worker: Notification clicked');
  
  event.notification.close();
  
  event.waitUntil(
    clients.openWindow('./tourism-guide.html')
  );
});

// Message handling from main app
self.addEventListener('message', (event) => {
  console.log('Service Worker: Message received:', event.data);
  
  if (event.data && event.data.type === 'SKIP_WAITING') {
    self.skipWaiting();
  }
});

// Utility functions
async function processOfflineAnalysis() {
  // Handle offline image analysis requests
  console.log('Service Worker: Processing offline analysis');
  // Implementation for when the app comes back online
}

// Cache management utilities
async function clearOldCaches() {
  const cacheNames = await caches.keys();
  const oldCaches = cacheNames.filter(name => 
    name.startsWith('tourism-') && name !== CACHE_NAME && name !== API_CACHE_NAME
  );
  
  return Promise.all(oldCaches.map(name => caches.delete(name)));
}

console.log('Service Worker: Script loaded successfully');