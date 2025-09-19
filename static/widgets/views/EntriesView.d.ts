import { FCOSOrchidJudgeWidget } from '../widget';
export declare class EntriesView {
    private widget;
    constructor(widget: FCOSOrchidJudgeWidget);
    render(): string;
    mount(container: HTMLElement): Promise<void>;
    private loadEntries;
    private renderEntry;
    private getDisplayName;
    private getBandClass;
    private viewEntry;
}
//# sourceMappingURL=EntriesView.d.ts.map