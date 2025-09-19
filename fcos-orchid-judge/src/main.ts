import { FCOSOrchidJudgeWidget } from './widget'
import { WidgetConfig } from './types'

// Global mounting API
const FCOSOrchidJudge = {
  mount(selector: string, config: Partial<WidgetConfig> = {}): FCOSOrchidJudgeWidget {
    const container = document.querySelector(selector) as HTMLElement
    if (!container) {
      throw new Error(`FCOS Orchid Judge: Container not found for selector "${selector}"`)
    }

    const defaultConfig: WidgetConfig = {
      theme: 'light',
      largeText: false,
      cloud: {
        webappUrl: window.EXPO_PUBLIC_FCOS_SHEETS_WEBAPP_URL || import.meta.env.EXPO_PUBLIC_FCOS_SHEETS_WEBAPP_URL,
        secret: window.EXPO_PUBLIC_FCOS_SHEETS_SECRET || import.meta.env.EXPO_PUBLIC_FCOS_SHEETS_SECRET
      },
      aiProvider: {
        mode: 'openai',
        webhookUrl: undefined
      },
      language: 'en'
    }

    const finalConfig = { ...defaultConfig, ...config }
    
    return new FCOSOrchidJudgeWidget(container, finalConfig)
  },

  unmount(widget: FCOSOrchidJudgeWidget): void {
    widget.destroy()
  }
}

// Export for module systems
export default FCOSOrchidJudge
export { FCOSOrchidJudgeWidget }

// Global for UMD builds
if (typeof window !== 'undefined') {
  (window as any).FCOSOrchidJudge = FCOSOrchidJudge
}