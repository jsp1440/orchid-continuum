import { FCOSOrchidJudgeWidget } from '../widget'
import { OrchidEntry } from '../types'

export class CertificateView {
  constructor(private widget: FCOSOrchidJudgeWidget) {}

  render(entry?: OrchidEntry): string {
    if (!entry) {
      return `
        <div class="text-center py-8">
          <div class="text-gray-500 dark:text-gray-400">No entry data available</div>
          <button class="btn btn-outline mt-4" data-action="back">← Back</button>
        </div>
      `
    }

    const displayName = this.getDisplayName(entry)
    const date = new Date(entry.timestamp).toLocaleDateString()
    const bandClass = this.getBandClass(entry.scoring.band)

    return `
      <div class="space-y-6">
        <!-- Header -->
        <div class="flex items-center gap-3 mb-6">
          <button class="btn btn-outline" data-action="back">← Back</button>
          <h2 class="text-xl font-bold text-gray-900 dark:text-white">Certificate</h2>
        </div>

        <!-- Certificate Display -->
        <div id="certificate-content" class="card">
          <!-- Header Section -->
          <div class="text-center mb-6">
            <h1 class="text-2xl font-bold text-gray-900 dark:text-white mb-2">
              FCOS Orchid Judge
            </h1>
            <p class="text-sm text-gray-600 dark:text-gray-400">
              Educational Judging Certificate
            </p>
          </div>

          <!-- Orchid Info -->
          <div class="border-b border-gray-200 dark:border-gray-700 pb-4 mb-4">
            <h2 class="text-xl font-semibold text-gray-900 dark:text-white mb-2">
              ${displayName}
            </h2>
            <div class="grid grid-cols-2 gap-4 text-sm">
              <div>
                <span class="text-gray-600 dark:text-gray-400">Genus:</span>
                <span class="ml-2 text-gray-900 dark:text-white">${entry.ocr.genus || 'Unknown'}</span>
              </div>
              <div>
                <span class="text-gray-600 dark:text-gray-400">Species/Grex:</span>
                <span class="ml-2 text-gray-900 dark:text-white">${entry.ocr.speciesOrGrex || 'Unknown'}</span>
              </div>
              ${entry.ocr.clone ? `
                <div class="col-span-2">
                  <span class="text-gray-600 dark:text-gray-400">Clone:</span>
                  <span class="ml-2 text-gray-900 dark:text-white">'${entry.ocr.clone}'</span>
                </div>
              ` : ''}
            </div>
          </div>

          <!-- Metrics Panel -->
          <div class="grid grid-cols-3 gap-4 mb-6">
            <div class="text-center">
              <div class="text-2xl font-bold text-primary-600 dark:text-primary-400">
                ${entry.analysis.spikeCount}
              </div>
              <div class="text-sm text-gray-600 dark:text-gray-400">Spike Count</div>
            </div>
            <div class="text-center">
              <div class="text-2xl font-bold text-primary-600 dark:text-primary-400">
                ${entry.analysis.symmetryPct}%
              </div>
              <div class="text-sm text-gray-600 dark:text-gray-400">Symmetry</div>
            </div>
            <div class="text-center">
              <div class="text-2xl font-bold text-primary-600 dark:text-primary-400">
                ${entry.analysis.naturalSpreadCm}cm
              </div>
              <div class="text-sm text-gray-600 dark:text-gray-400">Natural Spread</div>
            </div>
          </div>

          <!-- Scoring Results -->
          <div class="mb-6">
            <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-3">
              Educational Scoring Results
            </h3>
            
            <div class="text-center mb-4">
              <div class="text-4xl font-bold text-gray-900 dark:text-white">
                ${entry.scoring.weightedTotal}/100
              </div>
              <div class="text-lg px-4 py-2 rounded-full inline-block mt-2 ${bandClass}">
                ${entry.scoring.band}
              </div>
            </div>

            <!-- Detailed Scores -->
            <div class="space-y-2 text-sm">
              ${this.renderScoreBreakdown(entry)}
            </div>
          </div>

          <!-- Footer -->
          <div class="text-center pt-4 border-t border-gray-200 dark:border-gray-700">
            <p class="text-sm text-gray-600 dark:text-gray-400 mb-1">
              Five Cities Orchid Society — Learn · Grow · Share
            </p>
            <p class="text-xs text-gray-500 dark:text-gray-500">
              Generated on ${date} • Educational purposes only
            </p>
          </div>
        </div>

        <!-- Export Actions -->
        <div class="space-y-4">
          <h3 class="text-lg font-semibold text-gray-900 dark:text-white">
            Export Options
          </h3>
          
          <div class="grid grid-cols-2 gap-3">
            <button class="btn btn-primary" data-action="export-png">
              📄 Certificate PNG
            </button>
            <button class="btn btn-outline" data-action="export-csv">
              📊 Score Report CSV
            </button>
            <button class="btn btn-outline" data-action="export-narrative">
              📝 Narrative TXT
            </button>
            <button class="btn btn-outline" data-action="export-hybrid">
              🧬 Hybrid Report TXT
            </button>
          </div>

          <!-- Email & Share -->
          <div class="card bg-gray-50 dark:bg-gray-800">
            <h4 class="font-medium text-gray-900 dark:text-white mb-3">
              Share Results
            </h4>
            <div class="space-y-3">
              <input type="email" class="input" id="share-email" 
                     placeholder="Email address (optional)">
              <div class="flex gap-2">
                <button class="btn btn-primary flex-1" data-action="share">
                  📧 Share
                </button>
                <button class="btn btn-outline" data-action="save-entry">
                  💾 Save Entry
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    `
  }

  private renderScoreBreakdown(entry: OrchidEntry): string {
    const categories = [
      { key: 'form', label: 'Form / Symmetry / Balance' },
      { key: 'color', label: 'Color & Saturation' },
      { key: 'size', label: 'Size / Substance' },
      { key: 'floriferousness', label: 'Floriferousness & Arrangement' },
      { key: 'condition', label: 'Condition & Grooming' },
      { key: 'distinctiveness', label: 'Distinctiveness / Impression' }
    ]

    return categories.map(cat => {
      const weight = entry.scoring.weights[cat.key as keyof typeof entry.scoring.weights]
      const raw = entry.scoring.raw[cat.key as keyof typeof entry.scoring.raw]
      const weighted = Math.round((raw / 100) * weight)
      
      return `
        <div class="flex justify-between items-center">
          <span class="text-gray-700 dark:text-gray-300">${cat.label}</span>
          <div class="text-right">
            <span class="text-gray-900 dark:text-white font-medium">${weighted}/${weight}</span>
            <span class="text-gray-500 dark:text-gray-400 ml-2">(${raw}/100)</span>
          </div>
        </div>
      `
    }).join('')
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

  mount(container: HTMLElement): void {
    // Set up event listeners
    const backBtn = container.querySelector('[data-action="back"]')
    
    backBtn?.addEventListener('click', () => this.widget.goBack())

    // Export buttons
    container.querySelector('[data-action="export-png"]')?.addEventListener('click', () => this.exportPNG())
    container.querySelector('[data-action="export-csv"]')?.addEventListener('click', () => this.exportCSV())
    container.querySelector('[data-action="export-narrative"]')?.addEventListener('click', () => this.exportNarrative())
    container.querySelector('[data-action="export-hybrid"]')?.addEventListener('click', () => this.exportHybrid())
    container.querySelector('[data-action="share"]')?.addEventListener('click', () => this.shareResults())
    container.querySelector('[data-action="save-entry"]')?.addEventListener('click', () => this.saveEntry())
  }

  private async exportPNG(): Promise<void> {
    try {
      // Dynamic import for html2canvas
      const html2canvas = (await import('html2canvas')).default
      
      const element = document.querySelector('#certificate-content') as HTMLElement
      if (!element) return

      const canvas = await html2canvas(element, {
        backgroundColor: '#ffffff',
        scale: 2,
        useCORS: true
      })

      // Download the image
      const link = document.createElement('a')
      link.download = `orchid-certificate-${Date.now()}.png`
      link.href = canvas.toDataURL()
      link.click()
    } catch (error) {
      console.error('Failed to export PNG:', error)
      alert('Failed to export certificate. Please try again.')
    }
  }

  private exportCSV(): void {
    // Implementation for CSV export would go here
    alert('CSV export functionality coming soon!')
  }

  private exportNarrative(): void {
    // Implementation for narrative export would go here
    alert('Narrative export functionality coming soon!')
  }

  private exportHybrid(): void {
    // Implementation for hybrid report export would go here
    alert('Hybrid report export functionality coming soon!')
  }

  private shareResults(): void {
    // Implementation for sharing would go here
    alert('Share functionality coming soon!')
  }

  private saveEntry(): void {
    // Implementation for saving entry would go here
    alert('Entry saved successfully!')
  }
}