const CACHE_NAME = 'fcos-judge-v1.0.0';
const CACHE_URLS = [
  '/fcos-judge/',
  '/fcos-judge/capture',
  '/static/css/fcos-judge.css',
  '/static/js/fcos-judge.js',
  '/static/js/photo-capture.js',
  '/static/js/ocr-analyzer.js',
  '/static/js/ai-analysis.js',
  '/static/manifest.json'
];

self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => cache.addAll(CACHE_URLS))
  );
});

self.addEventListener('fetch', event => {
  event.respondWith(
    caches.match(event.request)
      .then(response => {
        // Return cached version or fetch from network
        return response || fetch(event.request);
      })
  );
});

// Background sync for offline submissions
self.addEventListener('sync', event => {
  if (event.tag === 'judge-submission') {
    event.waitUntil(syncSubmissions());
  }
});

async function syncSubmissions() {
  const db = await openDB();
  const submissions = await db.getAll('pending_submissions');
  
  for (const submission of submissions) {
    try {
      await fetch('/api/fcos-judge/submit', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(submission.data)
      });
      await db.delete('pending_submissions', submission.id);
    } catch (error) {
      console.log('Sync failed, will retry:', error);
    }
  }
}

function openDB() {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open('FCOSJudgeDB', 1);
    request.onerror = () => reject(request.error);
    request.onsuccess = () => resolve(request.result);
    request.onupgradeneeded = event => {
      const db = event.target.result;
      if (!db.objectStoreNames.contains('pending_submissions')) {
        db.createObjectStore('pending_submissions', { keyPath: 'id', autoIncrement: true });
      }
    };
  });
}