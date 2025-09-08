import { OrchidEntry, Profile } from '../types';
declare class StorageManager {
    private dbName;
    private dbVersion;
    private db;
    init(): Promise<void>;
    isAvailable(): boolean;
    saveEntry(entry: OrchidEntry): Promise<void>;
    getEntries(limit?: number): Promise<OrchidEntry[]>;
    getEntry(id: string): Promise<OrchidEntry | null>;
    saveProfile(profile: Profile): void;
    getProfile(): Profile | null;
    private getEntriesFromLocalStorage;
    clearAll(): Promise<void>;
}
export declare const storage: StorageManager;
export {};
//# sourceMappingURL=storage.d.ts.map