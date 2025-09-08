import { WidgetConfig, ViewState, ViewType } from './types'
import { HomeView } from './views/HomeView'
import { ProfileView } from './views/ProfileView'
import { CaptureView } from './views/CaptureView'
import { EntriesView } from './views/EntriesView'
import { CertificateView } from './views/CertificateView'
import { HowToView } from './views/HowToView'
import { FAQView } from './views/FAQView'
import { AboutView } from './views/AboutView'
import './styles/tailwind.css'

export class FCOSOrchidJudgeWidget {
  private container: HTMLElement
  private config: WidgetConfig
  private viewState: ViewState
  private views: Map<ViewType, any>

  constructor(container: HTMLElement, config: WidgetConfig) {
    this.container = container
    this.config = config
    this.viewState = { currentView: 'home' }
    this.views = new Map()
    
    this.initializeWidget()
    this.initializeViews()
    this.applyTheme()
    this.render()
  }

  private initializeWidget(): void {
    this.container.className = `fcos-orchid-judge ${this.config.theme} ${this.config.largeText ? 'large-text' : ''}`
    this.container.innerHTML = `
      <div class="widget-container">
        <div id="fcos-header" class="sticky top-0 z-10 bg-white dark:bg-gray-900 border-b border-gray-200 dark:border-gray-700 px-4 py-3">
          <div class="flex items-center justify-between">
            <h1 class="text-xl font-bold text-gray-900 dark:text-white">FCOS Orchid Judge</h1>
            <div class="flex gap-2">
              <button id="theme-toggle" class="btn btn-outline text-xs">
                ${this.config.theme === 'dark' ? '☀️' : '🌙'}
              </button>
              <button id="text-size-toggle" class="btn btn-outline text-xs">
                Aa ${this.config.largeText ? 'Normal' : 'Large'}
              </button>
            </div>
          </div>
        </div>
        <div id="fcos-content" class="px-4 py-6"></div>
        <div id="fcos-footer" class="px-4 py-3 border-t border-gray-200 dark:border-gray-700 text-center text-xs text-gray-500">
          Five Cities Orchid Society — Learn · Grow · Share
        </div>
      </div>
    `

    this.setupEventListeners()
  }

  private initializeViews(): void {
    this.views.set('home', new HomeView(this))
    this.views.set('profile', new ProfileView(this))
    this.views.set('capture', new CaptureView(this))
    this.views.set('entries', new EntriesView(this))
    this.views.set('certificate', new CertificateView(this))
    this.views.set('howto', new HowToView(this))
    this.views.set('faq', new FAQView(this))
    this.views.set('about', new AboutView(this))
  }

  private setupEventListeners(): void {
    const themeToggle = this.container.querySelector('#theme-toggle')
    const textSizeToggle = this.container.querySelector('#text-size-toggle')

    themeToggle?.addEventListener('click', () => {
      this.config.theme = this.config.theme === 'dark' ? 'light' : 'dark'
      this.applyTheme()
      this.updateHeader()
    })

    textSizeToggle?.addEventListener('click', () => {
      this.config.largeText = !this.config.largeText
      this.applyTextSize()
      this.updateHeader()
    })
  }

  private applyTheme(): void {
    if (this.config.theme === 'dark') {
      this.container.classList.add('dark')
    } else {
      this.container.classList.remove('dark')
    }
  }

  private applyTextSize(): void {
    if (this.config.largeText) {
      this.container.classList.add('large-text')
    } else {
      this.container.classList.remove('large-text')
    }
  }

  private updateHeader(): void {
    const themeToggle = this.container.querySelector('#theme-toggle')
    const textSizeToggle = this.container.querySelector('#text-size-toggle')
    
    if (themeToggle) {
      themeToggle.textContent = this.config.theme === 'dark' ? '☀️' : '🌙'
    }
    
    if (textSizeToggle) {
      textSizeToggle.textContent = `Aa ${this.config.largeText ? 'Normal' : 'Large'}`
    }
  }

  private render(): void {
    const contentEl = this.container.querySelector('#fcos-content') as HTMLElement
    if (!contentEl) return

    const currentView = this.views.get(this.viewState.currentView as ViewType)
    if (currentView) {
      contentEl.innerHTML = currentView.render(this.viewState.data)
      currentView.mount?.(contentEl)
    }
  }

  public navigateTo(view: ViewType, data?: any): void {
    this.viewState.previousView = this.viewState.currentView
    this.viewState.currentView = view
    this.viewState.data = data
    this.render()
  }

  public goBack(): void {
    if (this.viewState.previousView) {
      this.navigateTo(this.viewState.previousView as ViewType)
    } else {
      this.navigateTo('home')
    }
  }

  public getConfig(): WidgetConfig {
    return this.config
  }

  public updateConfig(updates: Partial<WidgetConfig>): void {
    this.config = { ...this.config, ...updates }
    this.applyTheme()
    this.applyTextSize()
    this.updateHeader()
  }

  public destroy(): void {
    this.container.innerHTML = ''
    this.views.clear()
  }
}