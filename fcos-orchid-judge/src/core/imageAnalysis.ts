export interface ImageAnalysisResult {
  flowerCount: number
  spikeCount: number
  symmetryPct: number
  confidence: number
  boundingBox?: {
    x: number
    y: number
    width: number
    height: number
  }
}

export class ImageAnalyzer {
  private canvas: HTMLCanvasElement
  private ctx: CanvasRenderingContext2D

  constructor() {
    this.canvas = document.createElement('canvas')
    this.ctx = this.canvas.getContext('2d')!
  }

  async analyzeImage(imageDataUrl: string): Promise<ImageAnalysisResult> {
    return new Promise((resolve) => {
      const img = new Image()
      img.onload = () => {
        // Set up canvas
        this.canvas.width = img.width
        this.canvas.height = img.height
        this.ctx.drawImage(img, 0, 0)

        const result = this.performAnalysis()
        resolve(result)
      }
      img.src = imageDataUrl
    })
  }

  private performAnalysis(): ImageAnalysisResult {
    const imageData = this.ctx.getImageData(0, 0, this.canvas.width, this.canvas.height)
    
    // Convert to grayscale
    const grayData = this.toGrayscale(imageData)
    
    // Apply Sobel edge detection
    const edges = this.sobelEdgeDetection(grayData)
    
    // Find the main flower region
    const boundingBox = this.findFlowerRegion(edges)
    
    // Calculate symmetry
    const symmetry = this.calculateSymmetry(edges, boundingBox)
    
    // Estimate flower count using blob detection
    const flowerCount = this.estimateFlowerCount(edges, boundingBox)
    
    return {
      flowerCount: Math.max(1, flowerCount),
      spikeCount: 1, // Default to 1, user can adjust
      symmetryPct: Math.round(symmetry * 100),
      confidence: 0.7, // Rough confidence estimate
      boundingBox
    }
  }

  private toGrayscale(imageData: ImageData): Uint8ClampedArray {
    const data = imageData.data
    const gray = new Uint8ClampedArray(imageData.width * imageData.height)
    
    for (let i = 0; i < data.length; i += 4) {
      const r = data[i]
      const g = data[i + 1]
      const b = data[i + 2]
      // Standard grayscale conversion
      gray[i / 4] = Math.round(0.299 * r + 0.587 * g + 0.114 * b)
    }
    
    return gray
  }

  private sobelEdgeDetection(grayData: Uint8ClampedArray): Uint8ClampedArray {
    const width = this.canvas.width
    const height = this.canvas.height
    const edges = new Uint8ClampedArray(width * height)
    
    // Sobel kernels
    const kernelX = [-1, 0, 1, -2, 0, 2, -1, 0, 1]
    const kernelY = [-1, -2, -1, 0, 0, 0, 1, 2, 1]
    
    for (let y = 1; y < height - 1; y++) {
      for (let x = 1; x < width - 1; x++) {
        let gx = 0, gy = 0
        
        for (let ky = -1; ky <= 1; ky++) {
          for (let kx = -1; kx <= 1; kx++) {
            const pixel = grayData[(y + ky) * width + (x + kx)]
            const kernelIndex = (ky + 1) * 3 + (kx + 1)
            gx += pixel * kernelX[kernelIndex]
            gy += pixel * kernelY[kernelIndex]
          }
        }
        
        const magnitude = Math.sqrt(gx * gx + gy * gy)
        edges[y * width + x] = Math.min(255, magnitude)
      }
    }
    
    return edges
  }

  private findFlowerRegion(edges: Uint8ClampedArray): { x: number; y: number; width: number; height: number } {
    const width = this.canvas.width
    const height = this.canvas.height
    
    // Find bounding box of significant edges
    let minX = width, maxX = 0, minY = height, maxY = 0
    let edgeCount = 0
    
    for (let y = 0; y < height; y++) {
      for (let x = 0; x < width; x++) {
        if (edges[y * width + x] > 50) { // Threshold for significant edges
          edgeCount++
          minX = Math.min(minX, x)
          maxX = Math.max(maxX, x)
          minY = Math.min(minY, y)
          maxY = Math.max(maxY, y)
        }
      }
    }
    
    // If no significant edges found, use center region
    if (edgeCount < 100) {
      const centerX = width / 2
      const centerY = height / 2
      const size = Math.min(width, height) * 0.6
      
      return {
        x: centerX - size / 2,
        y: centerY - size / 2,
        width: size,
        height: size
      }
    }
    
    // Add some padding
    const padding = Math.min(width, height) * 0.1
    
    return {
      x: Math.max(0, minX - padding),
      y: Math.max(0, minY - padding),
      width: Math.min(width, maxX - minX + 2 * padding),
      height: Math.min(height, maxY - minY + 2 * padding)
    }
  }

  private calculateSymmetry(edges: Uint8ClampedArray, boundingBox: { x: number; y: number; width: number; height: number }): number {
    const width = this.canvas.width
    const { x: bx, y: by, width: bw, height: bh } = boundingBox
    
    // Focus on the central region for symmetry analysis
    const centerX = bx + bw / 2
    const analysisWidth = Math.floor(bw * 0.8) // Use 80% of bounding box width
    const startX = Math.floor(centerX - analysisWidth / 2)
    
    let totalDiff = 0
    let pixelCount = 0
    
    for (let y = Math.floor(by); y < Math.floor(by + bh); y++) {
      for (let x = 0; x < Math.floor(analysisWidth / 2); x++) {
        const leftX = startX + x
        const rightX = startX + analysisWidth - x - 1
        
        if (leftX >= 0 && rightX < width && y >= 0 && y < this.canvas.height) {
          const leftPixel = edges[y * width + leftX]
          const rightPixel = edges[y * width + rightX]
          totalDiff += Math.abs(leftPixel - rightPixel)
          pixelCount++
        }
      }
    }
    
    if (pixelCount === 0) return 0.5
    
    // Normalize difference to 0-1 range (lower difference = higher symmetry)
    const avgDiff = totalDiff / pixelCount
    const maxPossibleDiff = 255
    const symmetryScore = 1 - (avgDiff / maxPossibleDiff)
    
    return Math.max(0, Math.min(1, symmetryScore))
  }

  private estimateFlowerCount(edges: Uint8ClampedArray, boundingBox: { x: number; y: number; width: number; height: number }): number {
    // Simple blob detection based on connected components
    const width = this.canvas.width
    const { x: bx, y: by, width: bw, height: bh } = boundingBox
    
    // Create binary image from edges
    const binary = new Uint8ClampedArray(width * this.canvas.height)
    for (let i = 0; i < edges.length; i++) {
      binary[i] = edges[i] > 80 ? 255 : 0 // Threshold for strong edges
    }
    
    // Find connected components within bounding box
    const visited = new Set<number>()
    let blobCount = 0
    const minBlobSize = Math.floor(bw * bh * 0.01) // Minimum 1% of bounding box area
    
    for (let y = Math.floor(by); y < Math.floor(by + bh); y += 3) { // Sample every 3rd pixel for performance
      for (let x = Math.floor(bx); x < Math.floor(bx + bw); x += 3) {
        const index = y * width + x
        
        if (!visited.has(index) && binary[index] === 255) {
          const blobSize = this.floodFill(binary, visited, x, y, width, this.canvas.height)
          
          if (blobSize > minBlobSize) {
            blobCount++
          }
        }
      }
    }
    
    // Estimate flowers based on blob count
    // Multiple blobs might represent one flower, so we use a heuristic
    if (blobCount <= 2) return 1
    if (blobCount <= 6) return Math.ceil(blobCount / 2)
    if (blobCount <= 12) return Math.ceil(blobCount / 3)
    
    return Math.min(20, Math.ceil(blobCount / 4)) // Cap at reasonable maximum
  }

  private floodFill(binary: Uint8ClampedArray, visited: Set<number>, startX: number, startY: number, width: number, height: number): number {
    const stack = [[startX, startY]]
    let size = 0
    
    while (stack.length > 0) {
      const [x, y] = stack.pop()!
      const index = y * width + x
      
      if (x < 0 || x >= width || y < 0 || y >= height || visited.has(index) || binary[index] !== 255) {
        continue
      }
      
      visited.add(index)
      size++
      
      // Add 4-connected neighbors
      stack.push([x + 1, y], [x - 1, y], [x, y + 1], [x, y - 1])
    }
    
    return size
  }
}

// Export singleton instance
export const imageAnalyzer = new ImageAnalyzer()