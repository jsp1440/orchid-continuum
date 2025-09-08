import { FCOSOrchidJudgeWidget } from '../widget'

export class HowToView {
  constructor(private widget: FCOSOrchidJudgeWidget) {}

  render(): string {
    return `
      <div class="space-y-6">
        <!-- Header -->
        <div class="flex items-center gap-3 mb-6">
          <button class="btn btn-outline" data-action="back">← Back</button>
          <h2 class="text-xl font-bold text-gray-900 dark:text-white">How to Use</h2>
        </div>

        <!-- Introduction -->
        <div class="card bg-blue-50 dark:bg-blue-900/20 border-blue-200 dark:border-blue-800">
          <h3 class="font-semibold text-blue-800 dark:text-blue-200 mb-2">
            Welcome to FCOS Orchid Judge
          </h3>
          <p class="text-sm text-blue-700 dark:text-blue-300">
            Follow these steps to create educational orchid judging entries. 
            This tool is designed for learning and practice purposes only.
          </p>
        </div>

        <!-- Steps -->
        <div class="space-y-4">
          ${this.renderStep(1, '📷', 'Capture Photos', 
            'Take clear photos of your blooming orchid and ID tag (if available)',
            'capture')}
          
          ${this.renderStep(2, '🏷️', 'Read the Tag', 
            'OCR extracts genus/species/grex/clone information from ID tags automatically',
            'capture')}
          
          ${this.renderStep(3, '📚', 'Registry Lookup', 
            'Optional lookup of parentage and awards from RHS/AOS databases',
            null)}
          
          ${this.renderStep(4, '🔍', 'Image Analysis', 
            'AI analyzes flower counts, symmetry, and measurements with manual editing',
            null)}
          
          ${this.renderStep(5, '⭐', 'Educational Scoring', 
            'Score using weighted educational rubric with instant band results',
            null)}
          
          ${this.renderStep(6, '📤', 'Export & Cloud', 
            'Generate certificates (PNG), reports (CSV/TXT) with optional cloud sync',
            null)}
          
          ${this.renderStep(7, '📋', 'History & Certificates', 
            'Review past entries and generate professional certificates',
            'entries')}
          
          ${this.renderStep(8, '🔒', 'Tips & Privacy', 
            'Data stays on your device unless cloud sync is enabled',
            null)}
        </div>

        <!-- Quick Start -->
        <div class="card bg-primary-50 dark:bg-primary-900/20 border-primary-200 dark:border-primary-800">
          <h3 class="font-semibold text-primary-800 dark:text-primary-200 mb-3">
            Ready to Begin?
          </h3>
          <button class="btn btn-primary w-full" data-action="quick-start">
            Start Your First Entry
          </button>
        </div>
      </div>
    `
  }

  private renderStep(number: number, icon: string, title: string, description: string, action: string | null): string {
    return `
      <div class="card">
        <div class="flex items-start gap-4">
          <div class="w-10 h-10 bg-primary-100 dark:bg-primary-800 rounded-full flex items-center justify-center flex-shrink-0">
            <span class="text-lg">${icon}</span>
          </div>
          
          <div class="flex-1">
            <div class="flex items-center justify-between mb-2">
              <h3 class="font-semibold text-gray-900 dark:text-white">
                ${number}. ${title}
              </h3>
              ${action ? `
                <button class="btn btn-outline btn-sm" data-action="step" data-step="${action}">
                  Start
                </button>
              ` : ''}
            </div>
            
            <p class="text-sm text-gray-600 dark:text-gray-400">
              ${description}
            </p>
          </div>
        </div>
      </div>
    `
  }

  mount(container: HTMLElement): void {
    // Set up event listeners
    const backBtn = container.querySelector('[data-action="back"]')
    const quickStartBtn = container.querySelector('[data-action="quick-start"]')
    
    backBtn?.addEventListener('click', () => this.widget.goBack())
    quickStartBtn?.addEventListener('click', () => this.widget.navigateTo('capture'))

    // Step navigation buttons
    container.querySelectorAll('[data-action="step"]').forEach(btn => {
      btn.addEventListener('click', (e) => {
        const step = (e.target as HTMLElement).dataset.step
        if (step) {
          this.widget.navigateTo(step as any)
        }
      })
    })
  }
}