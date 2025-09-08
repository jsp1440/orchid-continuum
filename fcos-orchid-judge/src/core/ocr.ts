import Tesseract from 'tesseract.js'

export interface OCRResult {
  genus: string
  speciesOrGrex: string
  clone: string
  isHybrid: boolean
  confidence: number
  rawText: string
}

export class OCRService {
  private worker: Tesseract.Worker | null = null

  async initialize(): Promise<void> {
    if (this.worker) return

    this.worker = await Tesseract.createWorker('eng')
    await this.worker.setParameters({
      tessedit_char_whitelist: 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789 .,()[]"\'×-',
    })
  }

  async extractText(imageDataUrl: string): Promise<OCRResult> {
    if (!this.worker) {
      await this.initialize()
    }

    try {
      const { data } = await this.worker!.recognize(imageDataUrl)
      const rawText = data.text.trim()
      
      return this.parseOrchidText(rawText, data.confidence)
    } catch (error) {
      console.error('OCR failed:', error)
      return {
        genus: '',
        speciesOrGrex: '',
        clone: '',
        isHybrid: false,
        confidence: 0,
        rawText: ''
      }
    }
  }

  private parseOrchidText(text: string, confidence: number): OCRResult {
    // Clean up the text
    const cleaned = text.replace(/[^\w\s.,()[\]"'×-]/g, ' ')
                       .replace(/\s+/g, ' ')
                       .trim()

    // Initialize result
    const result: OCRResult = {
      genus: '',
      speciesOrGrex: '',
      clone: '',
      isHybrid: false,
      confidence: confidence,
      rawText: text
    }

    // Split into lines and process
    const lines = cleaned.split('\n').map(line => line.trim()).filter(line => line.length > 0)
    
    if (lines.length === 0) return result

    // Look for the main orchid name (usually the first or second line)
    let mainLine = lines[0]
    
    // Check if first line looks like a genus name
    if (mainLine.length < 3 || !this.isCapitalized(mainLine.split(' ')[0])) {
      mainLine = lines[1] || lines[0]
    }

    // Parse the main line
    this.parseMainName(mainLine, result)

    // Look for clone name in quotes or parentheses
    const allText = lines.join(' ')
    this.parseCloneName(allText, result)

    // Detect if it's a hybrid (contains ×, 'x', or common hybrid indicators)
    result.isHybrid = this.detectHybrid(allText)

    return result
  }

  private parseMainName(text: string, result: OCRResult): void {
    const words = text.split(/\s+/).filter(word => word.length > 0)
    
    if (words.length >= 1) {
      // First word is usually the genus
      result.genus = this.capitalizeFirst(words[0].replace(/[^\w]/g, ''))
    }
    
    if (words.length >= 2) {
      // Second word is species or grex name
      result.speciesOrGrex = words[1].replace(/[^\w]/g, '').toLowerCase()
      
      // If there are more words, they might be part of the species/grex name
      if (words.length > 2) {
        const additionalWords = words.slice(2, 4) // Take at most 2 more words
          .filter(word => !this.isCloneIndicator(word))
          .map(word => word.replace(/[^\w]/g, '').toLowerCase())
        
        if (additionalWords.length > 0) {
          result.speciesOrGrex += ' ' + additionalWords.join(' ')
        }
      }
    }
  }

  private parseCloneName(text: string, result: OCRResult): void {
    // Look for text in quotes
    const quoteMatches = text.match(/["']([^"']+)["']/g)
    if (quoteMatches && quoteMatches.length > 0) {
      result.clone = quoteMatches[0].replace(/["']/g, '').trim()
      return
    }

    // Look for text in parentheses (but not hybrid parentheses)
    const parenMatches = text.match(/\(([^)]+)\)/g)
    if (parenMatches && parenMatches.length > 0) {
      for (const match of parenMatches) {
        const content = match.replace(/[()]/g, '').trim()
        // Skip if it looks like a hybrid cross
        if (!content.includes('×') && !content.includes(' x ')) {
          result.clone = content
          break
        }
      }
    }
  }

  private detectHybrid(text: string): boolean {
    const hybridIndicators = [
      '×', 'x ', ' x ', 'X ', ' X ',
      'hybrid', 'cross', 'grex'
    ]
    
    const lowerText = text.toLowerCase()
    return hybridIndicators.some(indicator => 
      lowerText.includes(indicator.toLowerCase())
    )
  }

  private isCapitalized(word: string): boolean {
    return word.length > 0 && word[0] === word[0].toUpperCase()
  }

  private capitalizeFirst(word: string): string {
    if (word.length === 0) return word
    return word[0].toUpperCase() + word.slice(1).toLowerCase()
  }

  private isCloneIndicator(word: string): boolean {
    const indicators = ['clone', 'cv', 'cultivar', '"', "'", '(', ')']
    const lowerWord = word.toLowerCase()
    return indicators.some(indicator => lowerWord.includes(indicator))
  }

  async terminate(): Promise<void> {
    if (this.worker) {
      await this.worker.terminate()
      this.worker = null
    }
  }
}

// Export singleton instance
export const ocrService = new OCRService()