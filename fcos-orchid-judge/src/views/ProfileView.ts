import { FCOSOrchidJudgeWidget } from '../widget'
import { Profile } from '../types'
import { storage } from '../core/storage'

export class ProfileView {
  constructor(private widget: FCOSOrchidJudgeWidget) {}

  render(): string {
    const profile = this.loadProfile()
    const config = this.widget.getConfig()
    
    return `
      <div class="space-y-6">
        <!-- Header -->
        <div class="flex items-center gap-3 mb-6">
          <button class="btn btn-outline" data-action="back">← Back</button>
          <h2 class="text-xl font-bold text-gray-900 dark:text-white">Profile & Settings</h2>
        </div>

        <!-- Profile Form -->
        <div class="card space-y-4">
          <h3 class="text-lg font-semibold text-gray-900 dark:text-white">Personal Information</h3>
          
          <div>
            <label class="label">Name</label>
            <input type="text" class="input" id="profile-name" value="${profile.name}" placeholder="Your name">
          </div>
          
          <div>
            <label class="label">Email (optional)</label>
            <input type="email" class="input" id="profile-email" value="${profile.email}" placeholder="your.email@example.com">
          </div>
          
          <div>
            <label class="label">Language</label>
            <select class="input" id="profile-language">
              <option value="en" ${profile.language === 'en' ? 'selected' : ''}>English</option>
              <option value="ja" ${profile.language === 'ja' ? 'selected' : ''}>Japanese</option>
            </select>
          </div>
        </div>

        <!-- AI Provider Settings -->
        <div class="card space-y-4">
          <h3 class="text-lg font-semibold text-gray-900 dark:text-white">AI Provider</h3>
          
          <div>
            <label class="label">Provider</label>
            <select class="input" id="ai-provider">
              <option value="openai" ${profile.aiProvider === 'openai' ? 'selected' : ''}>OpenAI</option>
              <option value="webhook" ${profile.aiProvider === 'webhook' ? 'selected' : ''}>Custom Webhook</option>
            </select>
          </div>
          
          <div id="webhook-url-container" class="${profile.aiProvider === 'webhook' ? '' : 'hidden'}">
            <label class="label">Webhook URL</label>
            <input type="url" class="input" id="webhook-url" value="${profile.webhookUrl || ''}" 
                   placeholder="https://your-api.com/analyze">
          </div>
          
          <div class="flex gap-2">
            <button class="btn btn-outline" data-action="test-ai">Test Connection</button>
            <button class="btn btn-outline" data-action="diagnostics">Run Diagnostics</button>
          </div>
          
          <div id="connection-status" class="text-sm"></div>
        </div>

        <!-- App Settings -->
        <div class="card space-y-4">
          <h3 class="text-lg font-semibold text-gray-900 dark:text-white">App Settings</h3>
          
          <div class="flex items-center justify-between">
            <div>
              <label class="label mb-0">Tutorial Mode</label>
              <p class="text-sm text-gray-600 dark:text-gray-400">Show helpful tips and guidance</p>
            </div>
            <input type="checkbox" id="tutorial-enabled" ${profile.tutorialEnabled ? 'checked' : ''} 
                   class="w-5 h-5 text-primary-600 rounded border-gray-300 focus:ring-primary-500">
          </div>
          
          <div class="flex items-center justify-between">
            <div>
              <label class="label mb-0">Cloud Sync</label>
              <p class="text-sm text-gray-600 dark:text-gray-400">
                ${config.cloud?.webappUrl ? 'Auto-upload entries to cloud' : 'Not configured'}
              </p>
            </div>
            <input type="checkbox" id="cloud-sync-enabled" ${profile.cloudSyncEnabled ? 'checked' : ''} 
                   ${!config.cloud?.webappUrl ? 'disabled' : ''}
                   class="w-5 h-5 text-primary-600 rounded border-gray-300 focus:ring-primary-500">
          </div>
        </div>

        <!-- Save Button -->
        <button class="btn btn-primary w-full" data-action="save">Save Profile</button>
      </div>
    `
  }

  mount(container: HTMLElement): void {
    // Set up event listeners
    const backBtn = container.querySelector('[data-action="back"]')
    const saveBtn = container.querySelector('[data-action="save"]')
    const testAiBtn = container.querySelector('[data-action="test-ai"]')
    const diagnosticsBtn = container.querySelector('[data-action="diagnostics"]')
    const aiProviderSelect = container.querySelector('#ai-provider') as HTMLSelectElement
    const webhookContainer = container.querySelector('#webhook-url-container')

    backBtn?.addEventListener('click', () => this.widget.goBack())
    saveBtn?.addEventListener('click', () => this.saveProfile(container))
    testAiBtn?.addEventListener('click', () => this.testAiConnection(container))
    diagnosticsBtn?.addEventListener('click', () => this.runDiagnostics(container))

    aiProviderSelect?.addEventListener('change', () => {
      const isWebhook = aiProviderSelect.value === 'webhook'
      webhookContainer?.classList.toggle('hidden', !isWebhook)
    })
  }

  private loadProfile(): Profile {
    const saved = storage.getProfile()
    return saved || {
      name: '',
      email: '',
      language: 'en',
      aiProvider: 'openai',
      tutorialEnabled: true,
      cloudSyncEnabled: false
    }
  }

  private saveProfile(container: HTMLElement): void {
    const profile: Profile = {
      name: (container.querySelector('#profile-name') as HTMLInputElement).value,
      email: (container.querySelector('#profile-email') as HTMLInputElement).value,
      language: (container.querySelector('#profile-language') as HTMLSelectElement).value as 'en' | 'ja',
      aiProvider: (container.querySelector('#ai-provider') as HTMLSelectElement).value as 'openai' | 'webhook',
      webhookUrl: (container.querySelector('#webhook-url') as HTMLInputElement).value,
      tutorialEnabled: (container.querySelector('#tutorial-enabled') as HTMLInputElement).checked,
      cloudSyncEnabled: (container.querySelector('#cloud-sync-enabled') as HTMLInputElement).checked
    }

    storage.saveProfile(profile)
    this.showStatus(container, 'Profile saved successfully!', 'success')
  }

  private async testAiConnection(container: HTMLElement): Promise<void> {
    const profile = this.loadProfile()
    const statusEl = container.querySelector('#connection-status') as HTMLElement

    statusEl.innerHTML = '<span class="text-blue-600">Testing connection...</span>'

    try {
      if (profile.aiProvider === 'openai') {
        // Test OpenAI connection
        const response = await fetch('https://api.openai.com/v1/models', {
          headers: {
            'Authorization': `Bearer ${window.OPENAI_API_KEY || ''}`
          }
        })
        
        if (response.ok) {
          statusEl.innerHTML = '<span class="text-green-600">✓ OpenAI connection successful</span>'
        } else {
          statusEl.innerHTML = '<span class="text-red-600">✗ OpenAI connection failed - check API key</span>'
        }
      } else {
        // Test webhook connection
        const response = await fetch(profile.webhookUrl || '', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ test: true })
        })
        
        if (response.ok) {
          statusEl.innerHTML = '<span class="text-green-600">✓ Webhook connection successful</span>'
        } else {
          statusEl.innerHTML = '<span class="text-red-600">✗ Webhook connection failed</span>'
        }
      }
    } catch (error) {
      statusEl.innerHTML = '<span class="text-red-600">✗ Connection test failed</span>'
    }
  }

  private async runDiagnostics(container: HTMLElement): Promise<void> {
    const statusEl = container.querySelector('#connection-status') as HTMLElement
    
    statusEl.innerHTML = `
      <div class="space-y-2 text-sm">
        <div class="font-semibold">System Diagnostics:</div>
        <div>• Storage: ${storage.isAvailable() ? '✓ Available' : '✗ Not available'}</div>
        <div>• Camera: ${navigator.mediaDevices ? '✓ Available' : '✗ Not available'}</div>
        <div>• Cloud: ${this.widget.getConfig().cloud?.webappUrl ? '✓ Configured' : '✗ Not configured'}</div>
        <div>• Web Share: ${navigator.share ? '✓ Available' : '✗ Not available'}</div>
        <div>• File System: ${(window as any).showSaveFilePicker ? '✓ Available' : '✗ Not available'}</div>
      </div>
    `
  }

  private showStatus(container: HTMLElement, message: string, type: 'success' | 'error'): void {
    const statusEl = container.querySelector('#connection-status') as HTMLElement
    const colorClass = type === 'success' ? 'text-green-600' : 'text-red-600'
    statusEl.innerHTML = `<span class="${colorClass}">${message}</span>`
    
    setTimeout(() => {
      statusEl.innerHTML = ''
    }, 3000)
  }
}