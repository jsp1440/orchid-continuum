import { FCOSOrchidJudgeWidget } from '../widget'
import { OrchidEntry } from '../types'

export class CaptureView {
  private currentEntry: Partial<OrchidEntry> = {}
  private stream: MediaStream | null = null

  constructor(private widget: FCOSOrchidJudgeWidget) {}

  render(): string {
    return `
      <div class="space-y-6">
        <!-- Header -->
        <div class="flex items-center gap-3 mb-6">
          <button class="btn btn-outline" data-action="back">← Back</button>
          <h2 class="text-xl font-bold text-gray-900 dark:text-white">Capture Photos</h2>
        </div>

        <!-- Educational Notice -->
        <div class="card bg-blue-50 dark:bg-blue-900/20 border-blue-200 dark:border-blue-800">
          <div class="flex items-start gap-3">
            <div class="text-blue-600 dark:text-blue-400 mt-1">ℹ️</div>
            <div>
              <h3 class="font-semibold text-blue-800 dark:text-blue-200 mb-1">Photo Tips</h3>
              <p class="text-sm text-blue-700 dark:text-blue-300">
                • Capture clear photos of the blooming plant<br>
                • Include the ID tag if available<br>
                • Good lighting improves analysis accuracy<br>
                • Include a ruler/card for size reference
              </p>
            </div>
          </div>
        </div>

        <!-- Photo Steps -->
        <div class="space-y-4">
          <!-- Step 1: Plant Photo -->
          <div class="card">
            <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">
              Step 1: Blooming Plant Photo
            </h3>
            
            <div id="plant-photo-section">
              ${this.currentEntry.photos?.plant ? this.renderPhotoPreview('plant') : this.renderPhotoCapture('plant')}
            </div>
          </div>

          <!-- Step 2: ID Tag Photo (Optional) -->
          <div class="card">
            <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">
              Step 2: ID Tag Photo (Optional)
            </h3>
            
            <div id="tag-photo-section">
              ${this.currentEntry.photos?.tag ? this.renderPhotoPreview('tag') : this.renderPhotoCapture('tag')}
            </div>
          </div>

          <!-- Continue Button -->
          <div class="pt-4">
            <button class="btn btn-primary w-full" data-action="continue" 
                    ${!this.currentEntry.photos?.plant ? 'disabled' : ''}>
              ${this.currentEntry.photos?.tag ? 'Continue to Tag Analysis' : 'Continue without Tag'}
            </button>
          </div>
        </div>
      </div>
    `
  }

  private renderPhotoCapture(type: 'plant' | 'tag'): string {
    return `
      <div class="space-y-3">
        <div class="grid grid-cols-2 gap-3">
          <button class="btn btn-primary" data-action="camera" data-type="${type}">
            📷 Take Photo
          </button>
          <button class="btn btn-outline" data-action="library" data-type="${type}">
            🖼️ Photo Library
          </button>
        </div>
        
        <!-- Camera Preview (hidden initially) -->
        <div id="${type}-camera-section" class="hidden">
          <video id="${type}-video" class="w-full rounded-lg bg-gray-100 dark:bg-gray-800" autoplay playsinline></video>
          <div class="flex gap-2 mt-3">
            <button class="btn btn-primary flex-1" data-action="take-photo" data-type="${type}">
              📸 Capture
            </button>
            <button class="btn btn-outline" data-action="cancel-camera" data-type="${type}">
              Cancel
            </button>
          </div>
          <canvas id="${type}-canvas" class="hidden"></canvas>
        </div>
        
        <!-- File Input (hidden) -->
        <input type="file" id="${type}-file-input" accept="image/*" class="hidden">
      </div>
    `
  }

  private renderPhotoPreview(type: 'plant' | 'tag'): string {
    const photo = type === 'plant' ? this.currentEntry.photos?.plant : this.currentEntry.photos?.tag
    return `
      <div class="space-y-3">
        <div class="relative">
          <img src="${photo}" alt="${type} photo" class="w-full rounded-lg">
          <button class="absolute top-2 right-2 btn btn-outline text-sm" data-action="retake" data-type="${type}">
            🔄 Retake
          </button>
        </div>
      </div>
    `
  }

  mount(container: HTMLElement): void {
    // Set up event listeners
    const backBtn = container.querySelector('[data-action="back"]')
    const continueBtn = container.querySelector('[data-action="continue"]')
    
    backBtn?.addEventListener('click', () => this.widget.goBack())
    continueBtn?.addEventListener('click', () => this.continueToAnalysis())

    // Camera and library buttons
    container.querySelectorAll('[data-action="camera"]').forEach(btn => {
      btn.addEventListener('click', (e) => {
        const type = (e.target as HTMLElement).dataset.type as 'plant' | 'tag'
        this.startCamera(type, container)
      })
    })

    container.querySelectorAll('[data-action="library"]').forEach(btn => {
      btn.addEventListener('click', (e) => {
        const type = (e.target as HTMLElement).dataset.type as 'plant' | 'tag'
        this.openPhotoLibrary(type, container)
      })
    })

    container.querySelectorAll('[data-action="take-photo"]').forEach(btn => {
      btn.addEventListener('click', (e) => {
        const type = (e.target as HTMLElement).dataset.type as 'plant' | 'tag'
        this.takePhoto(type, container)
      })
    })

    container.querySelectorAll('[data-action="cancel-camera"]').forEach(btn => {
      btn.addEventListener('click', (e) => {
        const type = (e.target as HTMLElement).dataset.type as 'plant' | 'tag'
        this.cancelCamera(type, container)
      })
    })

    container.querySelectorAll('[data-action="retake"]').forEach(btn => {
      btn.addEventListener('click', (e) => {
        const type = (e.target as HTMLElement).dataset.type as 'plant' | 'tag'
        this.retakePhoto(type, container)
      })
    })
  }

  private async startCamera(type: 'plant' | 'tag', container: HTMLElement): Promise<void> {
    try {
      const constraints = {
        video: {
          facingMode: 'environment', // Use back camera on mobile
          width: { ideal: 1280 },
          height: { ideal: 720 }
        }
      }

      this.stream = await navigator.mediaDevices.getUserMedia(constraints)
      
      const video = container.querySelector(`#${type}-video`) as HTMLVideoElement
      const cameraSection = container.querySelector(`#${type}-camera-section`)
      
      if (video && cameraSection) {
        video.srcObject = this.stream
        cameraSection.classList.remove('hidden')
      }
    } catch (error) {
      console.error('Camera access failed:', error)
      alert('Camera access failed. Please check permissions and try again.')
    }
  }

  private takePhoto(type: 'plant' | 'tag', container: HTMLElement): void {
    const video = container.querySelector(`#${type}-video`) as HTMLVideoElement
    const canvas = container.querySelector(`#${type}-canvas`) as HTMLCanvasElement
    
    if (video && canvas) {
      const ctx = canvas.getContext('2d')
      canvas.width = video.videoWidth
      canvas.height = video.videoHeight
      
      ctx?.drawImage(video, 0, 0)
      
      const dataUrl = canvas.toDataURL('image/jpeg', 0.8)
      this.savePhoto(type, dataUrl)
      this.cancelCamera(type, container)
      this.updatePhotoSection(type, container)
    }
  }

  private cancelCamera(type: 'plant' | 'tag', container: HTMLElement): void {
    if (this.stream) {
      this.stream.getTracks().forEach(track => track.stop())
      this.stream = null
    }
    
    const cameraSection = container.querySelector(`#${type}-camera-section`)
    cameraSection?.classList.add('hidden')
  }

  private openPhotoLibrary(type: 'plant' | 'tag', container: HTMLElement): void {
    const fileInput = container.querySelector(`#${type}-file-input`) as HTMLInputElement
    
    fileInput.onchange = (e) => {
      const file = (e.target as HTMLInputElement).files?.[0]
      if (file) {
        const reader = new FileReader()
        reader.onload = (e) => {
          const dataUrl = e.target?.result as string
          this.savePhoto(type, dataUrl)
          this.updatePhotoSection(type, container)
        }
        reader.readAsDataURL(file)
      }
    }
    
    fileInput.click()
  }

  private savePhoto(type: 'plant' | 'tag', dataUrl: string): void {
    if (!this.currentEntry.photos) {
      this.currentEntry.photos = { plant: '' }
    }
    
    if (type === 'plant') {
      this.currentEntry.photos.plant = dataUrl
    } else {
      this.currentEntry.photos.tag = dataUrl
    }
  }

  private retakePhoto(type: 'plant' | 'tag', container: HTMLElement): void {
    if (type === 'plant') {
      this.currentEntry.photos!.plant = ''
    } else {
      this.currentEntry.photos!.tag = ''
    }
    
    this.updatePhotoSection(type, container)
  }

  private updatePhotoSection(type: 'plant' | 'tag', container: HTMLElement): void {
    const section = container.querySelector(`#${type}-photo-section`)
    if (section) {
      const hasPhoto = type === 'plant' ? this.currentEntry.photos?.plant : this.currentEntry.photos?.tag
      section.innerHTML = hasPhoto ? this.renderPhotoPreview(type) : this.renderPhotoCapture(type)
      
      // Re-attach event listeners for the updated section
      this.attachSectionListeners(section, type, container)
    }
    
    // Update continue button
    const continueBtn = container.querySelector('[data-action="continue"]') as HTMLButtonElement
    if (continueBtn) {
      continueBtn.disabled = !this.currentEntry.photos?.plant
      continueBtn.textContent = this.currentEntry.photos?.tag ? 'Continue to Tag Analysis' : 'Continue without Tag'
    }
  }

  private attachSectionListeners(section: Element, type: 'plant' | 'tag', container: HTMLElement): void {
    section.querySelectorAll('[data-action="camera"]').forEach(btn => {
      btn.addEventListener('click', () => this.startCamera(type, container))
    })

    section.querySelectorAll('[data-action="library"]').forEach(btn => {
      btn.addEventListener('click', () => this.openPhotoLibrary(type, container))
    })

    section.querySelectorAll('[data-action="take-photo"]').forEach(btn => {
      btn.addEventListener('click', () => this.takePhoto(type, container))
    })

    section.querySelectorAll('[data-action="cancel-camera"]').forEach(btn => {
      btn.addEventListener('click', () => this.cancelCamera(type, container))
    })

    section.querySelectorAll('[data-action="retake"]').forEach(btn => {
      btn.addEventListener('click', () => this.retakePhoto(type, container))
    })
  }

  private continueToAnalysis(): void {
    // Generate entry ID and timestamp
    this.currentEntry.id = this.generateId()
    this.currentEntry.timestamp = new Date().toISOString()
    
    // Navigate to analysis view (we'll create this next)
    this.widget.navigateTo('analysis' as any, this.currentEntry)
  }

  private generateId(): string {
    return 'entry_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9)
  }

  // Clean up when view is destroyed
  destroy(): void {
    if (this.stream) {
      this.stream.getTracks().forEach(track => track.stop())
      this.stream = null
    }
  }
}