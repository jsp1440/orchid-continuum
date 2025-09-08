/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly EXPO_PUBLIC_FCOS_SHEETS_WEBAPP_URL?: string
  readonly EXPO_PUBLIC_FCOS_SHEETS_SECRET?: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}

declare global {
  interface Window {
    EXPO_PUBLIC_FCOS_SHEETS_WEBAPP_URL?: string
    EXPO_PUBLIC_FCOS_SHEETS_SECRET?: string
    OPENAI_API_KEY?: string
    FCOSOrchidJudge?: any
  }
}