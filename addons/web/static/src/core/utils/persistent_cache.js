import { Deferred } from "@web/core/utils/concurrency";
import { IndexedDB } from "@web/core/utils/indexed_db";

class RamCache {
    constructor() {
        this.ram = {};
    }

    write(table, key, value) {
        if (!(table in this.ram)) {
            this.ram[table] = {};
        }
        this.ram[table][key] = value;
    }

    read(table, key) {
        return this.ram[table]?.[key];
    }

    delete(table, key) {
        delete this.ram[table]?.[key];
    }

    invalidate(tables = null) {
        if (tables) {
            tables = typeof tables === "string" ? [tables] : tables;
            for (const table of tables) {
                if (table in this.ram) {
                    this.ram[table] = {};
                }
            }
        } else {
            this.ram = {};
        }
    }
}

export class PersistentCache {
    constructor(name, version) {
        this.indexedDB = new IndexedDB(name, version);
        this.ramCache = new RamCache();
    }

    read(table, key, fallback, { onUpdate }) {
        const ramValue = this.ramCache.read(table, key);
        if (ramValue && !onUpdate) {
            return ramValue;
        }
        const def = new Deferred();
        let fromCache = false;
        const prom = fallback()
            .then((result) => {
                this.indexedDB.write(table, key, result);
                this.ramCache.write(table, key, Promise.resolve(result));
                def.resolve(result);
                if (onUpdate && fromCache && fromCache !== JSON.stringify(result)) {
                    onUpdate(result);
                }
                return result;
            })
            .catch((error) => {
                if (fromCache) {
                    throw error;
                }
                this.ramCache.delete(table, key);
                def.reject(error);
            });
        if (ramValue) {
            ramValue.then((value) => {
                fromCache = JSON.stringify(value);
                def.resolve(value);
            });
        } else {
            this.ramCache.write(table, key, prom);
            this.indexedDB.read(table, key).then((result) => {
                if (result) {
                    fromCache = JSON.stringify(result);
                    this.ramCache.write(table, key, Promise.resolve(result));
                    def.resolve(result);
                }
            });
        }
        return def;
    }

    invalidate(tables) {
        this.indexedDB.invalidate(tables);
        this.ramCache.invalidate(tables);
    }
}
