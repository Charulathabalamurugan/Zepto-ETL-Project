/**
 * Advanced Stock Availability API Server
 * Features: Parent-Child SKU Hierarchy, Caching, Performance Optimization
 */

const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const compression = require('compression');
const NodeCache = require('node-cache');
const Database = require('./database/config');

class AdvancedStockAPI {
    constructor() {
        this.app = express();
        this.db = new Database();
        this.cache = new NodeCache({ stdTTL: 300 }); // 5 minutes TTL
        this.port = process.env.PORT || 5000;
        
        this.setupMiddleware();
        this.setupRoutes();
        this.setupErrorHandling();
    }

    setupMiddleware() {
        // Security and performance middleware
        this.app.use(helmet());
        this.app.use(compression());
        this.app.use(cors());
        this.app.use(express.json({ limit: '10mb' }));
        this.app.use(express.urlencoded({ extended: true }));
        
        // Request logging middleware
        this.app.use((req, res, next) => {
            console.log(`${new Date().toISOString()} - ${req.method} ${req.path}`);
            next();
        });
    }

    setupRoutes() {
        // Health check
        this.app.get('/api/health-advanced', this.healthCheck.bind(this));
        
        // Main stock availability API
        this.app.post('/api/stock-availability-advanced', this.stockAvailabilityAdvanced.bind(this));
        
        // Performance benchmarking
        this.app.get('/api/performance-benchmark', this.performanceBenchmark.bind(this));
        
        // Cache management
        this.app.get('/api/cache-stats', this.cacheStats.bind(this));
        this.app.post('/api/clear-cache', this.clearCache.bind(this));
        
        // Data analysis endpoints
        this.app.get('/api/data-summary', this.dataSummary.bind(this));
        this.app.get('/api/hierarchy-overview', this.hierarchyOverview.bind(this));
    }

    setupErrorHandling() {
        // 404 handler
        this.app.use('*', (req, res) => {
            res.status(404).json({
                error: 'Endpoint not found',
                available_endpoints: [
                    'POST /api/stock-availability-advanced',
                    'GET /api/performance-benchmark',
                    'GET /api/cache-stats',
                    'POST /api/clear-cache',
                    'GET /api/health-advanced'
                ]
            });
        });

        // Global error handler
        this.app.use((err, req, res, next) => {
            console.error('Error:', err);
            res.status(500).json({
                error: 'Internal server error',
                message: err.message,
                timestamp: new Date().toISOString()
            });
        });
    }

    // Cache decorator function
    withCache(key, ttl = 300) {
        return (target, propertyName, descriptor) => {
            const method = descriptor.value;
            descriptor.value = async function(...args) {
                const cacheKey = typeof key === 'function' ? key(...args) : key;
                
                // Try to get from cache
                const cached = this.cache.get(cacheKey);
                if (cached) {
                    return { ...cached, cache_used: true };
                }
                
                // Execute method and cache result
                const result = await method.apply(this, args);
                this.cache.set(cacheKey, { ...result, cache_used: false }, ttl);
                
                return { ...result, cache_used: false };
            };
            return descriptor;
        };
    }

    async calculateParentMetrics(parentSku, cityName) {
        const cacheQuery = `
            SELECT * FROM parent_sku_cache 
            WHERE parent_sku = ? AND city_name = ?
        `;
        
        const cacheResult = await this.db.get(cacheQuery, [parentSku, cityName]);
        
        if (!cacheResult) {
            return null;
        }
        
        const avgInstock = cacheResult.avg_instock_darkstores;
        const avgTotal = cacheResult.avg_total_darkstores;
        const sumStock = cacheResult.sum_total_stock;
        const avgSales = cacheResult.avg_daily_sales;
        const childCount = cacheResult.child_count;
        const outOfStockChildren = cacheResult.out_of_stock_children;
        
        // Calculate parent metrics according to requirements
        const parentPercentage = avgTotal > 0 ? (avgInstock / avgTotal) * 100 : 0;
        const parentDaysOfStock = avgSales > 0 ? sumStock / avgSales : 0;
        const parentOutOfStock = outOfStockChildren === childCount;
        
        return {
            instock_darkstores: Math.round(avgInstock),
            total_darkstores: Math.round(avgTotal),
            instock_darkstores_percentage: Math.round(parentPercentage * 100) / 100,
            total_stock: sumStock,
            days_of_stock: Math.round(parentDaysOfStock * 100) / 100,
            out_of_stock_flag: parentOutOfStock
        };
    }

    async getChildrenMetrics(parentSku, cityName) {
        const childrenQuery = `
            SELECT 
                child_sku,
                stock_quantity,
                instock_darkstores,
                oos_darkstores,
                total_darkstores,
                average_daily_sales
            FROM stock_data_optimized
            WHERE parent_sku = ? AND city_name = ?
            ORDER BY child_sku
        `;
        
        const childrenRecords = await this.db.all(childrenQuery, [parentSku, cityName]);
        
        return childrenRecords.map(child => {
            const instock = child.instock_darkstores;
            const oos = child.oos_darkstores;
            const totalDarkstores = child.total_darkstores;
            const stockQuantity = child.stock_quantity;
            const avgSales = child.average_daily_sales;
            
            const childPercentage = totalDarkstores > 0 ? (instock / totalDarkstores) * 100 : 0;
            const childDays = avgSales > 0 ? stockQuantity / avgSales : 0;
            
            return {
                sku: child.child_sku,
                instock_darkstores: instock,
                out_of_stock_darkstores: oos,
                total_darkstores: totalDarkstores,
                instock_darkstores_percentage: Math.round(childPercentage * 100) / 100,
                total_stock: stockQuantity,
                days_of_stock: Math.round(childDays * 100) / 100,
                out_of_stock_flag: stockQuantity === 0
            };
        });
    }

    async getOptimizedStockData(filters) {
        const startTime = Date.now();
        
        // Build optimized query
        let query = `
            SELECT DISTINCT parent_sku, product_name, category, city_name
            FROM stock_data_optimized 
            WHERE 1=1
        `;
        const params = [];
        
        // Apply filters
        if (filters.city) {
            query += ' AND city_name = ?';
            params.push(filters.city.toLowerCase());
        }
        
        if (filters.skus && filters.skus.length > 0) {
            const placeholders = filters.skus.map(() => '?').join(',');
            query += ` AND parent_sku IN (${placeholders})`;
            params.push(...filters.skus);
        }
        
        if (filters.search) {
            query += ' AND (product_name LIKE ? OR category LIKE ?)';
            params.push(`%${filters.search}%`, `%${filters.search}%`);
        }
        
        // Apply sorting
        const sortColumnMap = {
            'SKU': 'parent_sku',
            'PRODUCT_NAME': 'product_name',
            'CATEGORY': 'category',
            'CITY': 'city_name'
        };
        const sortColumn = sortColumnMap[filters.sortBy?.toUpperCase()] || 'parent_sku';
        query += ` ORDER BY ${sortColumn} ${filters.sortOrder || 'ASC'}`;
        
        // Apply pagination
        const offset = (filters.page - 1) * filters.pageSize;
        query += ` LIMIT ${filters.pageSize} OFFSET ${offset}`;
        
        const parentRecords = await this.db.all(query, params);
        
        // Build hierarchical response
        const stockData = [];
        
        for (const parentRecord of parentRecords) {
            const parentSku = parentRecord.parent_sku;
            const cityName = parentRecord.city_name;
            
            const parentMetrics = await this.calculateParentMetrics(parentSku, cityName);
            
            if (parentMetrics) {
                const children = await this.getChildrenMetrics(parentSku, cityName);
                
                stockData.push({
                    sku: parentSku,
                    ...parentMetrics,
                    children: children
                });
            }
        }
        
        const executionTime = Date.now() - startTime;
        
        return {
            data: stockData,
            execution_time: executionTime,
            cache_used: false
        };
    }

    async stockAvailabilityAdvanced(req, res) {
        try {
            const filters = {
                city: req.body.city,
                skus: req.body.skus || [],
                page: req.body.page || 1,
                pageSize: req.body.pageSize || 10,
                sortBy: req.body.sortBy || 'sku',
                sortOrder: req.body.sortOrder?.toUpperCase() || 'ASC',
                search: req.body.search || ''
            };
            
            console.log(`Advanced API Request: city=${filters.city}, skus=${filters.skus.length}, search='${filters.search}'`);
            
            // Create cache key
            const cacheKey = `stock_data_${JSON.stringify(filters)}`;
            
            // Try cache first
            let result = this.cache.get(cacheKey);
            let cacheUsed = true;
            
            if (!result) {
                result = await this.getOptimizedStockData(filters);
                this.cache.set(cacheKey, result, 300); // 5 minutes
                cacheUsed = false;
            }
            
            res.json({
                city: filters.city,
                data: result.data,
                performance: {
                    execution_time_ms: result.execution_time,
                    cache_used: cacheUsed,
                    total_results: result.data.length
                }
            });
            
        } catch (error) {
            console.error('Stock availability error:', error);
            res.status(500).json({
                error: error.message,
                performance: { execution_time_ms: 0, cache_used: false }
            });
        }
    }

    async performanceBenchmark(req, res) {
        try {
            const testQueries = [
                { city: 'delhi', pageSize: 5 },
                { search: 'Baby', pageSize: 10 },
                { skus: ['SKU1', 'SKU2'], pageSize: 3 },
                { city: 'mumbai', sortBy: 'SKU', pageSize: 7 }
            ];
            
            const benchmarkResults = [];
            
            for (let i = 0; i < testQueries.length; i++) {
                const query = testQueries[i];
                
                // Clear cache for accurate timing
                this.cache.flushAll();
                
                // Time the first run
                const startTime = Date.now();
                const result = await this.getOptimizedStockData(query);
                const firstRunTime = Date.now() - startTime;
                
                // Cache the result
                const cacheKey = `stock_data_${JSON.stringify(query)}`;
                this.cache.set(cacheKey, result, 300);
                
                // Time the cached run
                const cachedStart = Date.now();
                this.cache.get(cacheKey);
                const cachedTime = Date.now() - cachedStart;
                
                const improvement = firstRunTime > 0 ? 
                    Math.round((firstRunTime - cachedTime) / firstRunTime * 100) : 0;
                
                benchmarkResults.push({
                    test: `Query ${i + 1}`,
                    query: query,
                    first_run_ms: firstRunTime,
                    cached_run_ms: cachedTime,
                    performance_improvement: `${improvement}%`,
                    results_count: result.data.length
                });
            }
            
            res.json({
                benchmark_results: benchmarkResults,
                optimization_features: [
                    'Database indexing on city_name, parent_sku, child_sku',
                    'Pre-calculated parent SKU aggregation cache',
                    'In-memory response caching (5 min TTL)',
                    'Optimized parent-child hierarchy queries',
                    'WAL mode for better SQLite performance'
                ]
            });
            
        } catch (error) {
            res.status(500).json({ error: error.message });
        }
    }

    async cacheStats(req, res) {
        const stats = this.cache.getStats();
        
        res.json({
            cache_entries: this.cache.keys().length,
            cache_keys: this.cache.keys().slice(0, 10),
            cache_stats: stats,
            cache_expiry_seconds: 300
        });
    }

    async clearCache(req, res) {
        this.cache.flushAll();
        res.json({ message: 'Cache cleared successfully' });
    }

    async dataSummary(req, res) {
        try {
            const summary = await this.db.get(`
                SELECT 
                    COUNT(DISTINCT parent_sku) as total_parent_skus,
                    COUNT(DISTINCT child_sku) as total_child_skus,
                    COUNT(DISTINCT city_name) as total_cities,
                    COUNT(*) as total_records,
                    AVG(stock_quantity) as avg_stock,
                    SUM(total_sales) as total_sales
                FROM stock_data_optimized
            `);
            
            const cityBreakdown = await this.db.all(`
                SELECT 
                    city_name,
                    COUNT(*) as records,
                    AVG(stock_quantity) as avg_stock,
                    SUM(total_sales) as total_sales
                FROM stock_data_optimized
                GROUP BY city_name
                ORDER BY total_sales DESC
            `);
            
            res.json({
                summary: {
                    ...summary,
                    avg_stock: Math.round(summary.avg_stock * 100) / 100,
                    total_sales: Math.round(summary.total_sales * 100) / 100
                },
                cities: cityBreakdown.map(city => ({
                    ...city,
                    avg_stock: Math.round(city.avg_stock * 100) / 100,
                    total_sales: Math.round(city.total_sales * 100) / 100
                }))
            });
            
        } catch (error) {
            res.status(500).json({ error: error.message });
        }
    }

    async hierarchyOverview(req, res) {
        try {
            const hierarchy = await this.db.all(`
                SELECT 
                    parent_sku,
                    product_name,
                    category,
                    COUNT(DISTINCT child_sku) as child_count,
                    COUNT(DISTINCT city_name) as city_count,
                    AVG(stock_quantity) as avg_stock,
                    SUM(total_sales) as total_sales
                FROM stock_data_optimized
                GROUP BY parent_sku
                ORDER BY total_sales DESC
            `);
            
            res.json({
                parent_sku_overview: hierarchy.map(item => ({
                    ...item,
                    avg_stock: Math.round(item.avg_stock * 100) / 100,
                    total_sales: Math.round(item.total_sales * 100) / 100
                }))
            });
            
        } catch (error) {
            res.status(500).json({ error: error.message });
        }
    }

    async healthCheck(req, res) {
        res.json({
            status: 'healthy',
            features: [
                'Parent-child SKU hierarchy',
                'Database indexing optimization',
                'In-memory caching',
                'Performance benchmarking',
                'Hierarchical JSON responses'
            ],
            cache_entries: this.cache.keys().length,
            timestamp: new Date().toISOString()
        });
    }

    async start() {
        try {
            // Connect to database
            await this.db.connect();
            
            // Start server
            this.app.listen(this.port, () => {
                console.log('🚀 Advanced Stock Availability API Server Started');
                console.log('=' .repeat(60));
                console.log(`📡 Server running on http://localhost:${this.port}`);
                console.log('');
                console.log('🎯 Features:');
                console.log('  ✓ Parent-child SKU hierarchy with aggregation');
                console.log('  ✓ Database indexing for fast queries');
                console.log('  ✓ In-memory caching (5 min TTL)');
                console.log('  ✓ Performance benchmarking');
                console.log('  ✓ Hierarchical JSON responses');
                console.log('');
                console.log('📋 Endpoints:');
                console.log('  POST /api/stock-availability-advanced - Advanced stock API');
                console.log('  GET  /api/performance-benchmark - Performance testing');
                console.log('  GET  /api/cache-stats - Cache statistics');
                console.log('  POST /api/clear-cache - Clear cache');
                console.log('  GET  /api/data-summary - Data overview');
                console.log('  GET  /api/hierarchy-overview - Parent-child hierarchy');
                console.log('  GET  /api/health-advanced - Health check');
                console.log('');
                console.log('💾 Data: ~3120 child SKU records across 10 parent SKUs');
                console.log('🏙️  Cities: Delhi, Mumbai, Bangalore, Chennai, Hyderabad');
            });
            
        } catch (error) {
            console.error('❌ Failed to start server:', error.message);
            process.exit(1);
        }
    }

    async stop() {
        this.db.close();
        console.log('Server stopped');
    }
}

// Handle graceful shutdown
process.on('SIGINT', () => {
    console.log('\n🛑 Shutting down server...');
    process.exit(0);
});

process.on('SIGTERM', () => {
    console.log('\n🛑 Shutting down server...');
    process.exit(0);
});

// Start server if called directly
if (require.main === module) {
    const server = new AdvancedStockAPI();
    server.start();
}

module.exports = AdvancedStockAPI;
