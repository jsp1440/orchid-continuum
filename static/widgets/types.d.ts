export interface WidgetConfig {
    theme: 'light' | 'dark';
    largeText: boolean;
    cloud?: {
        webappUrl?: string;
        secret?: string;
    };
    aiProvider: {
        mode: 'openai' | 'webhook';
        webhookUrl?: string;
    };
    language: 'en' | 'ja';
}
export interface Profile {
    name: string;
    email: string;
    language: 'en' | 'ja';
    aiProvider: 'openai' | 'webhook';
    webhookUrl?: string;
    tutorialEnabled: boolean;
    cloudSyncEnabled: boolean;
}
export interface OrchidEntry {
    id: string;
    timestamp: string;
    photos: {
        plant: string;
        tag?: string;
    };
    ocr: {
        genus: string;
        speciesOrGrex: string;
        clone: string;
        isHybrid: boolean;
    };
    registry?: {
        parentage?: string;
        awards: string[];
    };
    analysis: {
        flowerCount: number;
        spikeCount: number;
        symmetryPct: number;
        naturalSpreadCm: number;
    };
    scoring: {
        weights: ScoringWeights;
        raw: ScoringRaw;
        weightedTotal: number;
        band: ScoreBand;
    };
    certificate?: {
        png: string;
    };
}
export interface ScoringWeights {
    form: number;
    color: number;
    size: number;
    floriferousness: number;
    condition: number;
    distinctiveness: number;
}
export interface ScoringRaw {
    form: number;
    color: number;
    size: number;
    floriferousness: number;
    condition: number;
    distinctiveness: number;
}
export type ScoreBand = 'no award (practice)' | 'Commended (educational)' | 'Distinction (educational)' | 'Excellence (educational)';
export interface CloudPayload {
    version: number;
    profile: Profile;
    entry: OrchidEntry;
    device: {
        ua: string;
    };
}
export interface RegistryAdapter {
    lookup(params: {
        genus: string;
        speciesOrGrex: string;
    }): Promise<{
        parentage?: string;
        awards: string[];
        found: boolean;
    }>;
}
export interface ViewState {
    currentView: string;
    previousView?: string;
    data?: any;
}
export type ViewType = 'home' | 'profile' | 'capture' | 'entries' | 'certificate' | 'howto' | 'faq' | 'about';
export interface DiagnosticResult {
    storage: boolean;
    camera: boolean;
    cloudEnv: boolean;
    freeSpace?: string;
    features: {
        webShare: boolean;
        fileSystem: boolean;
    };
    aiConnection?: boolean;
}
//# sourceMappingURL=types.d.ts.map