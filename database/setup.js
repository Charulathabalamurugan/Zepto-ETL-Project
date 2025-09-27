/**
 * Database Setup and Data Loading Script
 * Creates parent-child SKU hierarchy from real stock data
 */

const fs = require('fs');
const csv = require('csv-parser');
const Database = require('./config');

class DataSetup {
    constructor() {
        this.db = new Database();
        
        // Parent-Child SKU mapping
        this.parentChildMap = {
            'SKU1': ['SKU-A1', 'SKU-A2', 'SKU-A3'],
            'SKU2': ['SKU-B1', 'SKU-B2'],
            'SKU3': ['SKU-C1', 'SKU-C2'],
            'SKU4': ['SKU-D1', 'SKU-D2', 'SKU-D3'],
            'SKU5': ['SKU-E1', 'SKU-E2'],
            'SKU6': ['SKU-F1', 'SKU-F2'],
            'SKU7': ['SKU-G1', 'SKU-G2', 'SKU-G3'],
            'SKU8': ['SKU-H1', 'SKU-H2'],
            'SKU9': ['SKU-I1', 'SKU-I2'],
            'SKU10': ['SKU-J1', 'SKU-J2', 'SKU-J3']
        };

        this.parentNames = {
            'SKU1': 'Baby Wipes Collection',
            'SKU2': 'Aloe Vera Wipes Series',
            'SKU3': 'Premium Care Line',
            'SKU4': 'Oral Care Collection',
            'SKU5': 'Baby Grooming Tools',
            'SKU6': 'Essential Care Items',
            'SKU7': 'Feeding Accessories',
            'SKU8': 'Gentle Care Wipes',
            'SKU9': 'Comfort Series',
            'SKU10': 'Complete Care Kit'
        };
    }

    async downloadRealStockData() {
        const axios = require('axios');
        
        const sheetId = "10lOoozWOf1paFpPTxUfx-cuqxXjbsmFh_DOr9mUAP3U";
        const gid = "248630542";
        const csvUrl = `https://docs.google.com/spreadsheets/d/${sheetId}/export?format=csv&gid=${gid}`;
        
        console.log('📥 Downloading real stock data from Google Sheets...');
        
        try {
            const response = await axios.get(csvUrl);
            fs.writeFileSync('stock_data_real.csv', response.data);
            console.log('✓ Downloaded stock_data_real.csv');
            return true;
        } catch (error) {
            console.error('❌ Error downloading data:', error.message);
            return false;
        }
    }

    async loadCSVData() {
        return new Promise((resolve, reject) => {
            const results = [];
            
            if (!fs.existsSync('stock_data_real.csv')) {
                reject(new Error('stock_data_real.csv not found. Run downloadRealStockData() first!'));
                return;
            }
            
            fs.createReadStream('stock_data_real.csv')
                .pipe(csv())
                .on('data', (data) => results.push(data))
                .on('end', () => {
                    console.log(`✓ Loaded ${results.length} records from CSV`);
                    resolve(results);
                })
                .on('error', reject);
        });
    }

    createChildRecords(originalRecord) {
        const originalSku = originalRecord.product_id;
        const childRecords = [];
        
        if (this.parentChildMap[originalSku]) {
            const parentSku = originalSku;
            const children = this.parentChildMap[originalSku];
            
            children.forEach((childSku, index) => {
                const variationFactor = (index + 1) * 0.7;
                
                const childRecord = {
                    date: originalRecord.date,
                    city_name: originalRecord.city_name.toLowerCase(),
                    parent_sku: parentSku,
                    child_sku: childSku,
                    product_name: this.parentNames[parentSku] || originalRecord.product_name,
                    category: originalRecord.category,
                    total_orders: Math.max(1, Math.floor(parseInt(originalRecord.total_orders) * variationFactor)),
                    total_sales: parseFloat(originalRecord.total_sales) * variationFactor,
                    stock_quantity: Math.max(0, Math.floor(parseInt(originalRecord.stock_quantity) * variationFactor)),
                    instock_darkstores: Math.max(1, Math.floor(parseInt(originalRecord.instock_darkstores) * variationFactor)),
                    oos_darkstores: Math.max(1, Math.floor(parseInt(originalRecord.OOS_darkstores) * variationFactor)),
                    total_darkstores: Math.floor(parseInt(originalRecord.total_darkstores) * variationFactor),
                    average_daily_sales: parseInt(originalRecord.total_orders) / 26
                };
                
                childRecords.push(childRecord);
            });
        }
        
        return childRecords;
    }

    async insertChildRecords(childRecords) {
        const insertQuery = `
            INSERT INTO stock_data_optimized 
            (date, city_name, parent_sku, child_sku, product_name, category, 
             total_orders, total_sales, stock_quantity, instock_darkstores, 
             oos_darkstores, total_darkstores, average_daily_sales)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        `;

        await this.db.beginTransaction();
        
        try {
            for (const record of childRecords) {
                await this.db.run(insertQuery, [
                    record.date, record.city_name, record.parent_sku, record.child_sku,
                    record.product_name, record.category, record.total_orders, record.total_sales,
                    record.stock_quantity, record.instock_darkstores, record.oos_darkstores,
                    record.total_darkstores, record.average_daily_sales
                ]);
            }
            
            await this.db.commit();
            console.log(`✓ Inserted ${childRecords.length} child SKU records`);
        } catch (error) {
            await this.db.rollback();
            throw error;
        }
    }

    async buildAggregationCache() {
        console.log('🔄 Building parent SKU aggregation cache...');
        
        // Clear existing cache
        await this.db.run('DELETE FROM parent_sku_cache');
        
        const aggregationQuery = `
            INSERT INTO parent_sku_cache 
            (city_name, parent_sku, avg_instock_darkstores, avg_total_darkstores, 
             sum_total_stock, avg_daily_sales, child_count, out_of_stock_children)
            SELECT 
                city_name,
                parent_sku,
                AVG(CAST(instock_darkstores AS REAL)) as avg_instock_darkstores,
                AVG(CAST(total_darkstores AS REAL)) as avg_total_darkstores,
                SUM(stock_quantity) as sum_total_stock,
                AVG(average_daily_sales) as avg_daily_sales,
                COUNT(*) as child_count,
                SUM(CASE WHEN stock_quantity = 0 THEN 1 ELSE 0 END) as out_of_stock_children
            FROM stock_data_optimized
            GROUP BY city_name, parent_sku
        `;
        
        await this.db.run(aggregationQuery);
        
        const cacheCount = await this.db.get('SELECT COUNT(*) as count FROM parent_sku_cache');
        console.log(`✓ Built aggregation cache with ${cacheCount.count} parent SKU entries`);
    }

    async analyzeData() {
        console.log('\n📊 DATA ANALYSIS');
        console.log('=' .repeat(50));
        
        const stats = await this.db.get(`
            SELECT 
                COUNT(DISTINCT parent_sku) as parent_skus,
                COUNT(DISTINCT child_sku) as child_skus,
                COUNT(DISTINCT city_name) as cities,
                COUNT(*) as total_records
            FROM stock_data_optimized
        `);
        
        console.log(`Parent SKUs: ${stats.parent_skus}`);
        console.log(`Child SKUs: ${stats.child_skus}`);
        console.log(`Cities: ${stats.cities}`);
        console.log(`Total Records: ${stats.total_records}`);
        
        const hierarchy = await this.db.all(`
            SELECT 
                parent_sku, 
                COUNT(DISTINCT child_sku) as children_count,
                AVG(stock_quantity) as avg_stock
            FROM stock_data_optimized
            GROUP BY parent_sku
            ORDER BY children_count DESC
        `);
        
        console.log('\nParent-Child Distribution:');
        hierarchy.forEach(row => {
            console.log(`  ${row.parent_sku}: ${row.children_count} children, avg stock: ${Math.round(row.avg_stock)}`);
        });
    }

    async run() {
        try {
            console.log('🚀 Starting Database Setup...');
            
            // Connect to database
            await this.db.connect();
            
            // Create tables and indexes
            await this.db.createTables();
            
            // Download real data if not exists
            if (!fs.existsSync('stock_data_real.csv')) {
                await this.downloadRealStockData();
            }
            
            // Load CSV data
            const csvData = await this.loadCSVData();
            
            // Transform to parent-child hierarchy
            let allChildRecords = [];
            csvData.forEach(record => {
                const childRecords = this.createChildRecords(record);
                allChildRecords = allChildRecords.concat(childRecords);
            });
            
            // Insert child records
            await this.insertChildRecords(allChildRecords);
            
            // Build aggregation cache
            await this.buildAggregationCache();
            
            // Analyze data
            await this.analyzeData();
            
            console.log('\n✅ Database setup complete!');
            console.log('Features:');
            console.log('  - Parent-child SKU hierarchy');
            console.log('  - Performance indexes');
            console.log('  - Aggregation cache');
            console.log('  - Query optimization ready');
            
        } catch (error) {
            console.error('❌ Setup failed:', error.message);
        } finally {
            this.db.close();
        }
    }
}

// Run setup if called directly
if (require.main === module) {
    const setup = new DataSetup();
    setup.run();
}

module.exports = DataSetup;
