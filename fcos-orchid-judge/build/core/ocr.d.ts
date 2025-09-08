export interface OCRResult {
    genus: string;
    speciesOrGrex: string;
    clone: string;
    isHybrid: boolean;
    confidence: number;
    rawText: string;
}
export declare class OCRService {
    private worker;
    initialize(): Promise<void>;
    extractText(imageDataUrl: string): Promise<OCRResult>;
    private parseOrchidText;
    private parseMainName;
    private parseCloneName;
    private detectHybrid;
    private isCapitalized;
    private capitalizeFirst;
    private isCloneIndicator;
    terminate(): Promise<void>;
}
export declare const ocrService: OCRService;
//# sourceMappingURL=ocr.d.ts.map