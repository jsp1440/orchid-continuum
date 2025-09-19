import { FCOSOrchidJudgeWidget } from '../widget'
import { OrchidEntry } from '../types'
import { storage } from '../core/storage'

export class EntriesView {
  constructor(private widget: FCOSOrchidJudgeWidget) {}

  render(): string {
    return `
      <div class="space-y-6">
        <!-- Header -->
        <div class="flex items-center gap-3 mb-6">
          <button class="btn btn-outline" data-action="back">← Back</button>
          <h2 class="text-xl font-bold text-gray-900 dark:text-white">My Last 10 Entries</h2>
        </div>

        <!-- Loading State -->
        <div id="entries-loading" class="text-center py-8">
          <div class="text-gray-500 dark:text-gray-400">Loading entries...</div>
        </div>

        <!-- Entries List -->
        <div id="entries-list" class="space-y-4 hidden">
          <!-- Entries will be populated here -->
        </div>

        <!-- Empty State -->
        <div id="entries-empty" class="text-center py-12 hidden">
          <div class="text-gray-500 dark:text-gray-400 mb-4">
            📋 No entries yet
          </div>
          <p class="text-sm text-gray-400 dark:text-gray-500 mb-6">
            Start your first orchid judging session to see entries here
          </p>
          <button class="btn btn-primary" data-action="start-new">
            Start New Entry
          </button>
        </div>
      </div>
    `
  }

  async mount(container: HTMLElement): Promise<void> {
    // Set up event listeners
    const backBtn = container.querySelector('[data-action="back"]')
    const startNewBtn = container.querySelector('[data-action="start-new"]')
    
    backBtn?.addEventListener('click', () => this.widget.goBack())
    startNewBtn?.addEventListener('click', () => this.widget.navigateTo('capture'))

    // Load and display entries
    await this.loadEntries(container)
  }

  private async loadEntries(container: HTMLElement): Promise<void> {
    const loadingEl = container.querySelector('#entries-loading')
    const listEl = container.querySelector('#entries-list')
    const emptyEl = container.querySelector('#entries-empty')

    try {
      const entries = await storage.getEntries(10)
      
      loadingEl?.classList.add('hidden')
      
      if (entries.length === 0) {
        emptyEl?.classList.remove('hidden')
      } else {
        listEl!.innerHTML = entries.map(entry => this.renderEntry(entry)).join('')
        listEl?.classList.remove('hidden')
        
        // Add click listeners to entries
        listEl?.querySelectorAll('[data-action="view-entry"]').forEach(btn => {
          btn.addEventListener('click', (e) => {
            const entryId = (e.target as HTMLElement).dataset.entryId
            if (entryId) {
              this.viewEntry(entryId)
            }
          })
        })
      }
    } catch (error) {
      console.error('Failed to load entries:', error)
      loadingEl!.innerHTML = `
        <div class="text-red-500 dark:text-red-400">
          Failed to load entries. Please try again.
        </div>
      `
    }
  }

  private renderEntry(entry: OrchidEntry): string {
    const date = new Date(entry.timestamp).toLocaleDateString()
    const time = new Date(entry.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    
    // Create display name
    const displayName = this.getDisplayName(entry)
    
    // Get score band styling
    const bandClass = this.getBandClass(entry.scoring.band)
    
    // Count attachments
    let attachmentCount = 0
    if (entry.photos.plant) attachmentCount++
    if (entry.photos.tag) attachmentCount++
    if (entry.certificate?.png) attachmentCount++
    
    return `
      <div class="card hover:shadow-md transition-shadow cursor-pointer" 
           data-action="view-entry" data-entry-id="${entry.id}">
        <div class="flex items-start gap-4">
          <!-- Thumbnail -->
          <div class="w-16 h-16 rounded-lg overflow-hidden bg-gray-100 dark:bg-gray-800 flex-shrink-0">
            ${entry.photos.plant ? 
              `<img src="${entry.photos.plant}" alt="Orchid" class="w-full h-full object-cover">` :
              `<div class="w-full h-full flex items-center justify-center text-gray-400">📷</div>`
            }
          </div>
          
          <!-- Content -->
          <div class="flex-1 min-w-0">
            <div class="flex items-start justify-between gap-2 mb-2">
              <h3 class="font-semibold text-gray-900 dark:text-white truncate">
                ${displayName}
              </h3>
              <span class="text-sm px-2 py-1 rounded-full ${bandClass} flex-shrink-0">
                ${entry.scoring.weightedTotal}/100
              </span>
            </div>
            
            <div class="flex items-center gap-4 text-sm text-gray-600 dark:text-gray-400 mb-2">
              <span>🏆 AOS (Educational)</span>
              <span>📅 ${date}</span>
              <span>🕒 ${time}</span>
            </div>
            
            <div class="flex items-center justify-between">
              <span class="text-xs px-2 py-1 rounded ${bandClass}">
                ${entry.scoring.band}
              </span>
              
              <div class="flex items-center gap-2 text-xs text-gray-500 dark:text-gray-400">
                ${attachmentCount > 0 ? `<span>📎 ${attachmentCount}</span>` : ''}
                <span class="text-green-600 dark:text-green-400">●</span>
                <span>Completed</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    `
  }

  private getDisplayName(entry: OrchidEntry): string {
    const { genus, speciesOrGrex, clone } = entry.ocr
    
    if (!genus && !speciesOrGrex) {
      return 'Unnamed Orchid'
    }
    
    let name = genus || 'Unknown'
    if (speciesOrGrex) {
      name += ' ' + speciesOrGrex
    }
    if (clone) {
      name += ` '${clone}'`
    }
    
    return name
  }

  private getBandClass(band: string): string {
    switch (band) {
      case 'Excellence (educational)':
        return 'score-band-excellence'
      case 'Distinction (educational)':
        return 'score-band-distinction'
      case 'Commended (educational)':
        return 'score-band-commended'
      default:
        return 'score-band-none'
    }
  }

  private async viewEntry(entryId: string): Promise<void> {
    try {
      const entry = await storage.getEntry(entryId)
      if (entry) {
        this.widget.navigateTo('certificate', entry)
      }
    } catch (error) {
      console.error('Failed to load entry:', error)
      alert('Failed to load entry. Please try again.')
    }
  }
}