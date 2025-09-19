import { FCOSOrchidJudgeWidget } from '../widget';
import { OrchidEntry } from '../types';
export declare class CertificateView {
    private widget;
    constructor(widget: FCOSOrchidJudgeWidget);
    render(entry?: OrchidEntry): string;
    private renderScoreBreakdown;
    private getDisplayName;
    private getBandClass;
    mount(container: HTMLElement): void;
    private exportPNG;
    private exportCSV;
    private exportNarrative;
    private exportHybrid;
    private shareResults;
    private saveEntry;
}
//# sourceMappingURL=CertificateView.d.ts.map