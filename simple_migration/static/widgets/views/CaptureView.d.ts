import { FCOSOrchidJudgeWidget } from '../widget';
export declare class CaptureView {
    private widget;
    private currentEntry;
    private stream;
    constructor(widget: FCOSOrchidJudgeWidget);
    render(): string;
    private renderPhotoCapture;
    private renderPhotoPreview;
    mount(container: HTMLElement): void;
    private startCamera;
    private takePhoto;
    private cancelCamera;
    private openPhotoLibrary;
    private savePhoto;
    private retakePhoto;
    private updatePhotoSection;
    private attachSectionListeners;
    private continueToAnalysis;
    private generateId;
    destroy(): void;
}
//# sourceMappingURL=CaptureView.d.ts.map