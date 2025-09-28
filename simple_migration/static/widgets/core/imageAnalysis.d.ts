export interface ImageAnalysisResult {
    flowerCount: number;
    spikeCount: number;
    symmetryPct: number;
    confidence: number;
    boundingBox?: {
        x: number;
        y: number;
        width: number;
        height: number;
    };
}
export declare class ImageAnalyzer {
    private canvas;
    private ctx;
    constructor();
    analyzeImage(imageDataUrl: string): Promise<ImageAnalysisResult>;
    private performAnalysis;
    private toGrayscale;
    private sobelEdgeDetection;
    private findFlowerRegion;
    private calculateSymmetry;
    private estimateFlowerCount;
    private floodFill;
}
export declare const imageAnalyzer: ImageAnalyzer;
//# sourceMappingURL=imageAnalysis.d.ts.map