/**
 * Database Configuration and Connection Management
 */

const sqlite3 = require('sqlite3').verbose();
const path = require('path');

const DATABASE_PATH = path.join(__dirname, '..', 'stock_data_optimized_node.db');

class Database {
    constructor() {
        this.db = null;
    }

    async connect() {
        return new Promise((resolve, reject) => {
            this.db = new sqlite3.Database(DATABASE_PATH, (err) => {
                if (err) {
                    console.error('Error connecting to database:', err.message);
                    reject(err);
                } else {
                    console.log('Connected to SQLite database');
                    this.enableWAL();
                    resolve();
                }
            });
        });
    }

    enableWAL() {
        // Enable WAL mode for better performance
        this.db.run('PRAGMA journal_mode = WAL;');
        this.db.run('PRAGMA synchronous = NORMAL;');
        this.db.run('PRAGMA cache_size = 10000;');
        this.db.run('PRAGMA temp_store = MEMORY;');
    }

    async createTables() {
        const createMainTable = `
            CREATE TABLE IF NOT EXISTS stock_data_optimized (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                city_name TEXT NOT NULL,
                parent_sku TEXT NOT NULL,
                child_sku TEXT NOT NULL,
                product_name TEXT NOT NULL,
                category TEXT NOT NULL,
                total_orders INTEGER DEFAULT 0,
                total_sales REAL DEFAULT 0,
                stock_quantity INTEGER DEFAULT 0,
                instock_darkstores INTEGER DEFAULT 0,
                oos_darkstores INTEGER DEFAULT 0,
                total_darkstores INTEGER DEFAULT 0,
                average_daily_sales REAL DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        `;

        const createCacheTable = `
            CREATE TABLE IF NOT EXISTS parent_sku_cache (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                city_name TEXT NOT NULL,
                parent_sku TEXT NOT NULL,
                avg_instock_darkstores REAL DEFAULT 0,
                avg_total_darkstores REAL DEFAULT 0,
                sum_total_stock INTEGER DEFAULT 0,
                avg_daily_sales REAL DEFAULT 0,
                child_count INTEGER DEFAULT 0,
                out_of_stock_children INTEGER DEFAULT 0,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(city_name, parent_sku)
            )
        `;

        const indexes = [
            'CREATE INDEX IF NOT EXISTS idx_city_name ON stock_data_optimized(city_name)',
            'CREATE INDEX IF NOT EXISTS idx_parent_sku ON stock_data_optimized(parent_sku)',
            'CREATE INDEX IF NOT EXISTS idx_child_sku ON stock_data_optimized(child_sku)',
            'CREATE INDEX IF NOT EXISTS idx_date ON stock_data_optimized(date)',
            'CREATE INDEX IF NOT EXISTS idx_category ON stock_data_optimized(category)',
            'CREATE INDEX IF NOT EXISTS idx_city_parent ON stock_data_optimized(city_name, parent_sku)',
            'CREATE INDEX IF NOT EXISTS idx_stock_quantity ON stock_data_optimized(stock_quantity)',
            'CREATE INDEX IF NOT EXISTS idx_cache_city_parent ON parent_sku_cache(city_name, parent_sku)'
        ];

        return new Promise((resolve, reject) => {
            this.db.serialize(() => {
                this.db.run(createMainTable);
                this.db.run(createCacheTable);
                
                indexes.forEach(indexQuery => {
                    this.db.run(indexQuery);
                });

                console.log('✓ Database tables and indexes created');
                resolve();
            });
        });
    }

    async run(query, params = []) {
        return new Promise((resolve, reject) => {
            this.db.run(query, params, function(err) {
                if (err) {
                    reject(err);
                } else {
                    resolve({ lastID: this.lastID, changes: this.changes });
                }
            });
        });
    }

    async get(query, params = []) {
        return new Promise((resolve, reject) => {
            this.db.get(query, params, (err, row) => {
                if (err) {
                    reject(err);
                } else {
                    resolve(row);
                }
            });
        });
    }

    async all(query, params = []) {
        return new Promise((resolve, reject) => {
            this.db.all(query, params, (err, rows) => {
                if (err) {
                    reject(err);
                } else {
                    resolve(rows);
                }
            });
        });
    }

    async beginTransaction() {
        return this.run('BEGIN TRANSACTION');
    }

    async commit() {
        return this.run('COMMIT');
    }

    async rollback() {
        return this.run('ROLLBACK');
    }

    close() {
        if (this.db) {
            this.db.close((err) => {
                if (err) {
                    console.error('Error closing database:', err.message);
                } else {
                    console.log('Database connection closed');
                }
            });
        }
    }
}

module.exports = Database;
