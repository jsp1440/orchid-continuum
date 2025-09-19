import { OrchidEntry, Profile } from '../types'

class StorageManager {
  private dbName = 'fcos_orchid_judge'
  private dbVersion = 1
  private db: IDBDatabase | null = null

  async init(): Promise<void> {
    if (!('indexedDB' in window)) {
      console.warn('IndexedDB not available, falling back to localStorage')
      return
    }

    return new Promise((resolve, reject) => {
      const request = indexedDB.open(this.dbName, this.dbVersion)
      
      request.onerror = () => reject(request.error)
      request.onsuccess = () => {
        this.db = request.result
        resolve()
      }
      
      request.onupgradeneeded = (event) => {
        const db = (event.target as IDBOpenDBRequest).result
        
        // Create entries store
        if (!db.objectStoreNames.contains('entries')) {
          const entriesStore = db.createObjectStore('entries', { keyPath: 'id' })
          entriesStore.createIndex('timestamp', 'timestamp', { unique: false })
        }
        
        // Create profile store
        if (!db.objectStoreNames.contains('profile')) {
          db.createObjectStore('profile', { keyPath: 'id' })
        }
      }
    })
  }

  isAvailable(): boolean {
    return 'indexedDB' in window || 'localStorage' in window
  }

  // Entry management
  async saveEntry(entry: OrchidEntry): Promise<void> {
    if (this.db) {
      return new Promise((resolve, reject) => {
        const transaction = this.db!.transaction(['entries'], 'readwrite')
        const store = transaction.objectStore('entries')
        const request = store.put(entry)
        
        request.onsuccess = () => resolve()
        request.onerror = () => reject(request.error)
      })
    } else {
      // Fallback to localStorage
      const entries = this.getEntriesFromLocalStorage()
      const index = entries.findIndex(e => e.id === entry.id)
      if (index >= 0) {
        entries[index] = entry
      } else {
        entries.push(entry)
      }
      localStorage.setItem('fcos_orchid_judge_entries', JSON.stringify(entries))
    }
  }

  async getEntries(limit = 10): Promise<OrchidEntry[]> {
    if (this.db) {
      return new Promise((resolve, reject) => {
        const transaction = this.db!.transaction(['entries'], 'readonly')
        const store = transaction.objectStore('entries')
        const index = store.index('timestamp')
        const request = index.openCursor(null, 'prev')
        
        const results: OrchidEntry[] = []
        let count = 0
        
        request.onsuccess = (event) => {
          const cursor = (event.target as IDBRequest).result
          if (cursor && count < limit) {
            results.push(cursor.value)
            count++
            cursor.continue()
          } else {
            resolve(results)
          }
        }
        
        request.onerror = () => reject(request.error)
      })
    } else {
      // Fallback to localStorage
      const entries = this.getEntriesFromLocalStorage()
      return entries
        .sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime())
        .slice(0, limit)
    }
  }

  async getEntry(id: string): Promise<OrchidEntry | null> {
    if (this.db) {
      return new Promise((resolve, reject) => {
        const transaction = this.db!.transaction(['entries'], 'readonly')
        const store = transaction.objectStore('entries')
        const request = store.get(id)
        
        request.onsuccess = () => resolve(request.result || null)
        request.onerror = () => reject(request.error)
      })
    } else {
      // Fallback to localStorage
      const entries = this.getEntriesFromLocalStorage()
      return entries.find(e => e.id === id) || null
    }
  }

  // Profile management
  saveProfile(profile: Profile): void {
    if (this.db) {
      const transaction = this.db.transaction(['profile'], 'readwrite')
      const store = transaction.objectStore('profile')
      store.put({ id: 'default', ...profile })
    } else {
      localStorage.setItem('fcos_orchid_judge_profile', JSON.stringify(profile))
    }
  }

  getProfile(): Profile | null {
    if (this.db) {
      // For IndexedDB, we need to make this async, but keeping sync for simplicity
      // In a real implementation, you'd want to cache the profile
      const stored = localStorage.getItem('fcos_orchid_judge_profile')
      return stored ? JSON.parse(stored) : null
    } else {
      const stored = localStorage.getItem('fcos_orchid_judge_profile')
      return stored ? JSON.parse(stored) : null
    }
  }

  // Helper methods
  private getEntriesFromLocalStorage(): OrchidEntry[] {
    const stored = localStorage.getItem('fcos_orchid_judge_entries')
    return stored ? JSON.parse(stored) : []
  }

  // Clear all data
  async clearAll(): Promise<void> {
    if (this.db) {
      return new Promise((resolve, reject) => {
        const transaction = this.db!.transaction(['entries', 'profile'], 'readwrite')
        
        transaction.objectStore('entries').clear()
        transaction.objectStore('profile').clear()
        
        transaction.oncomplete = () => resolve()
        transaction.onerror = () => reject(transaction.error)
      })
    } else {
      localStorage.removeItem('fcos_orchid_judge_entries')
      localStorage.removeItem('fcos_orchid_judge_profile')
    }
  }
}

// Create singleton instance
export const storage = new StorageManager()

// Initialize storage when module loads
storage.init().catch(console.error)