import { WidgetConfig, ViewType } from './types';
export declare class FCOSOrchidJudgeWidget {
    private container;
    private config;
    private viewState;
    private views;
    constructor(container: HTMLElement, config: WidgetConfig);
    private initializeWidget;
    private initializeViews;
    private setupEventListeners;
    private applyTheme;
    private applyTextSize;
    private updateHeader;
    private render;
    navigateTo(view: ViewType, data?: any): void;
    goBack(): void;
    getConfig(): WidgetConfig;
    updateConfig(updates: Partial<WidgetConfig>): void;
    destroy(): void;
}
//# sourceMappingURL=widget.d.ts.map