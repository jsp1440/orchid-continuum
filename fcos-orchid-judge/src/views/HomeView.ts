import { FCOSOrchidJudgeWidget } from '../widget'

export class HomeView {
  constructor(private widget: FCOSOrchidJudgeWidget) {}

  render(): string {
    const config = this.widget.getConfig()
    const cloudEnabled = !!(config.cloud?.webappUrl && config.cloud?.secret)
    
    return `
      <div class="space-y-6">
        <!-- Educational Disclaimer -->
        <div class="card bg-amber-50 dark:bg-amber-900/20 border-amber-200 dark:border-amber-800">
          <div class="flex items-start gap-3">
            <div class="text-amber-600 dark:text-amber-400 mt-1">⚠️</div>
            <div>
              <h3 class="font-semibold text-amber-800 dark:text-amber-200 mb-1">Educational Tool Only</h3>
              <p class="text-sm text-amber-700 dark:text-amber-300">
                This judging system is for educational and practice purposes only. 
                It does not provide official awards from any recognized orchid organization.
              </p>
            </div>
          </div>
        </div>

        <!-- Cloud Status -->
        ${!cloudEnabled ? `
          <div class="card bg-amber-50 dark:bg-amber-900/20 border-amber-200 dark:border-amber-800">
            <div class="text-sm text-amber-700 dark:text-amber-300">
              <strong>Cloud sync disabled</strong> — add EXPO_PUBLIC_FCOS_SHEETS_WEBAPP_URL and EXPO_PUBLIC_FCOS_SHEETS_SECRET to enable
            </div>
          </div>
        ` : ''}

        <!-- Main Navigation Cards -->
        <div class="grid grid-cols-1 gap-4">
          <!-- Profile / ID -->
          <div class="nav-card-green" data-nav="profile">
            <div class="flex items-center gap-3">
              <div class="w-10 h-10 bg-primary-100 dark:bg-primary-800 rounded-lg flex items-center justify-center">
                <span class="text-primary-600 dark:text-primary-400">👤</span>
              </div>
              <div>
                <h3 class="font-semibold text-gray-900 dark:text-white">Profile / ID</h3>
                <p class="text-sm text-gray-600 dark:text-gray-400">Configure settings and AI provider</p>
              </div>
            </div>
          </div>

          <!-- Start New Entry -->
          <div class="nav-card-purple" data-nav="capture">
            <div class="flex items-center gap-3">
              <div class="w-10 h-10 bg-secondary-100 dark:bg-secondary-800 rounded-lg flex items-center justify-center">
                <span class="text-secondary-600 dark:text-secondary-400">📷</span>
              </div>
              <div>
                <h3 class="font-semibold text-gray-900 dark:text-white">Start New Entry</h3>
                <p class="text-sm text-gray-600 dark:text-gray-400">Capture photos and begin judging</p>
              </div>
            </div>
          </div>

          <!-- View My Last 10 -->
          <div class="nav-card" data-nav="entries">
            <div class="flex items-center gap-3">
              <div class="w-10 h-10 bg-gray-100 dark:bg-gray-800 rounded-lg flex items-center justify-center">
                <span class="text-gray-600 dark:text-gray-400">📋</span>
              </div>
              <div>
                <h3 class="font-semibold text-gray-900 dark:text-white">View My Last 10</h3>
                <p class="text-sm text-gray-600 dark:text-gray-400">Recent judging entries</p>
              </div>
            </div>
          </div>

          <!-- How to Use -->
          <div class="nav-card" data-nav="howto">
            <div class="flex items-center gap-3">
              <div class="w-10 h-10 bg-gray-100 dark:bg-gray-800 rounded-lg flex items-center justify-center">
                <span class="text-gray-600 dark:text-gray-400">❓</span>
              </div>
              <div>
                <h3 class="font-semibold text-gray-900 dark:text-white">How to Use</h3>
                <p class="text-sm text-gray-600 dark:text-gray-400">Step-by-step guide</p>
              </div>
            </div>
          </div>

          <!-- FAQ -->
          <div class="nav-card" data-nav="faq">
            <div class="flex items-center gap-3">
              <div class="w-10 h-10 bg-gray-100 dark:bg-gray-800 rounded-lg flex items-center justify-center">
                <span class="text-gray-600 dark:text-gray-400">💬</span>
              </div>
              <div>
                <h3 class="font-semibold text-gray-900 dark:text-white">FAQ</h3>
                <p class="text-sm text-gray-600 dark:text-gray-400">Frequently asked questions</p>
              </div>
            </div>
          </div>

          <!-- About -->
          <div class="nav-card" data-nav="about">
            <div class="flex items-center gap-3">
              <div class="w-10 h-10 bg-gray-100 dark:bg-gray-800 rounded-lg flex items-center justify-center">
                <span class="text-gray-600 dark:text-gray-400">ℹ️</span>
              </div>
              <div>
                <h3 class="font-semibold text-gray-900 dark:text-white">About</h3>
                <p class="text-sm text-gray-600 dark:text-gray-400">FCOS mission and disclaimers</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    `
  }

  mount(container: HTMLElement): void {
    // Add click handlers for navigation cards
    const navCards = container.querySelectorAll('[data-nav]')
    navCards.forEach(card => {
      card.addEventListener('click', () => {
        const nav = card.getAttribute('data-nav')
        if (nav) {
          this.widget.navigateTo(nav as any)
        }
      })
    })
  }
}