/**
 * Advanced Stock API Testing Suite
 * Tests parent-child hierarchy, performance, and all endpoints
 */

const axios = require('axios');

class APITester {
    constructor(baseURL = 'http://localhost:5000') {
        this.baseURL = baseURL;
        this.client = axios.create({ 
            baseURL,
            timeout: 30000,
            headers: { 'Content-Type': 'application/json' }
        });
    }

    async testHealthCheck() {
        console.log('\n🔍 Testing Health Check...');
        console.log('-'.repeat(40));
        
        try {
            const response = await this.client.get('/api/health-advanced');
            
            if (response.status === 200) {
                console.log('✅ Health check passed');
                console.log(`Status: ${response.data.status}`);
                console.log(`Features: ${response.data.features.length}`);
                console.log(`Cache entries: ${response.data.cache_entries}`);
                return true;
            }
        } catch (error) {
            console.log('❌ Health check failed:', error.message);
            return false;
        }
    }

    async testAdvancedStockAPI() {
        console.log('\n🔍 Testing Advanced Stock API...');
        console.log('-'.repeat(40));
        
        const testCases = [
            {
                name: 'Test 1: Delhi city stock with hierarchy',
                payload: {
                    city: 'Delhi',
                    page: 1,
                    pageSize: 3,
                    search: ''
                }
            },
            {
                name: 'Test 2: Search baby wipes products',
                payload: {
                    city: 'Mumbai',
                    page: 1,
                    pageSize: 2,
                    search: 'Baby Wipes'
                }
            },
            {
                name: 'Test 3: Specific parent SKUs',
                payload: {
                    skus: ['SKU1', 'SKU2'],
                    page: 1,
                    pageSize: 2,
                    sortBy: 'SKU',
                    sortOrder: 'ASC'
                }
            },
            {
                name: 'Test 4: Category search with sorting',
                payload: {
                    city: 'Bangalore',
                    search: 'Oral',
                    sortBy: 'PRODUCT_NAME',
                    sortOrder: 'DESC',
                    pageSize: 3
                }
            }
        ];
        
        for (const testCase of testCases) {
            console.log(`\n${testCase.name}`);
            console.log('-'.repeat(30));
            
            try {
                const response = await this.client.post('/api/stock-availability-advanced', testCase.payload);
                
                if (response.status === 200) {
                    const data = response.data;
                    console.log(`✅ Success!`);
                    console.log(`   City: ${data.city || 'All'}`);
                    console.log(`   Results: ${data.data.length}`);
                    console.log(`   Execution time: ${data.performance.execution_time_ms}ms`);
                    console.log(`   Cache used: ${data.performance.cache_used}`);
                    
                    // Validate parent-child structure
                    if (data.data.length > 0) {
                        const firstResult = data.data[0];
                        console.log(`   Sample Parent SKU: ${firstResult.sku}`);
                        console.log(`   Parent stock: ${firstResult.total_stock}`);
                        console.log(`   Parent percentage: ${firstResult.instock_darkstores_percentage}%`);
                        console.log(`   Children count: ${firstResult.children.length}`);
                        
                        if (firstResult.children.length > 0) {
                            const firstChild = firstResult.children[0];
                            console.log(`   Sample Child: ${firstChild.sku} (Stock: ${firstChild.total_stock})`);
                        }
                    }
                    
                    // Validate response structure
                    this.validateResponseStructure(data);
                    
                } else {
                    console.log(`❌ Failed: ${response.status}`);
                }
                
            } catch (error) {
                console.log(`❌ Request failed:`, error.response?.data || error.message);
            }
            
            // Small delay between tests
            await this.sleep(500);
        }
    }

    validateResponseStructure(data) {
        const requiredFields = ['city', 'data', 'performance'];
        const missingFields = requiredFields.filter(field => !(field in data));
        
        if (missingFields.length > 0) {
            console.log(`   ⚠️  Missing fields: ${missingFields.join(', ')}`);
        }
        
        if (data.data && data.data.length > 0) {
            const parentFields = ['sku', 'instock_darkstores', 'instock_darkstores_percentage', 
                                'total_darkstores', 'total_stock', 'days_of_stock', 
                                'out_of_stock_flag', 'children'];
            const parent = data.data[0];
            const missingParentFields = parentFields.filter(field => !(field in parent));
            
            if (missingParentFields.length === 0) {
                console.log(`   ✅ Parent structure valid`);
            } else {
                console.log(`   ⚠️  Parent missing: ${missingParentFields.join(', ')}`);
            }
            
            if (parent.children && parent.children.length > 0) {
                const childFields = ['sku', 'instock_darkstores', 'out_of_stock_darkstores', 
                                   'total_darkstores', 'instock_darkstores_percentage', 
                                   'total_stock', 'days_of_stock', 'out_of_stock_flag'];
                const child = parent.children[0];
                const missingChildFields = childFields.filter(field => !(field in child));
                
                if (missingChildFields.length === 0) {
                    console.log(`   ✅ Child structure valid`);
                } else {
                    console.log(`   ⚠️  Child missing: ${missingChildFields.join(', ')}`);
                }
            }
        }
    }

    async testPerformanceBenchmark() {
        console.log('\n🔍 Testing Performance Benchmark...');
        console.log('-'.repeat(40));
        
        try {
            const response = await this.client.get('/api/performance-benchmark');
            
            if (response.status === 200) {
                const data = response.data;
                console.log('✅ Performance benchmark completed');
                console.log('\nBenchmark Results:');
                
                data.benchmark_results.forEach((result, index) => {
                    console.log(`  ${result.test}:`);
                    console.log(`    Query: ${JSON.stringify(result.query)}`);
                    console.log(`    First run: ${result.first_run_ms}ms`);
                    console.log(`    Cached run: ${result.cached_run_ms}ms`);
                    console.log(`    Improvement: ${result.performance_improvement}`);
                    console.log(`    Results: ${result.results_count}`);
                    console.log('');
                });
                
                console.log('Optimization Features:');
                data.optimization_features.forEach(feature => {
                    console.log(`  ✓ ${feature}`);
                });
                
            } else {
                console.log(`❌ Benchmark failed: ${response.status}`);
            }
            
        } catch (error) {
            console.log('❌ Benchmark error:', error.response?.data || error.message);
        }
    }

    async testCacheOperations() {
        console.log('\n🔍 Testing Cache Operations...');
        console.log('-'.repeat(40));
        
        try {
            // Get cache stats
            let response = await this.client.get('/api/cache-stats');
            console.log(`✅ Cache stats: ${response.data.cache_entries} entries`);
            
            // Make a request to populate cache
            await this.client.post('/api/stock-availability-advanced', { 
                city: 'Delhi', 
                pageSize: 2 
            });
            
            // Check cache again
            response = await this.client.get('/api/cache-stats');
            console.log(`✅ Cache after request: ${response.data.cache_entries} entries`);
            
            // Clear cache
            response = await this.client.post('/api/clear-cache');
            console.log(`✅ Cache cleared: ${response.data.message}`);
            
            // Verify cache cleared
            response = await this.client.get('/api/cache-stats');
            console.log(`✅ Cache after clear: ${response.data.cache_entries} entries`);
            
        } catch (error) {
            console.log('❌ Cache operations error:', error.response?.data || error.message);
        }
    }

    async testDataSummary() {
        console.log('\n🔍 Testing Data Summary...');
        console.log('-'.repeat(40));
        
        try {
            const response = await this.client.get('/api/data-summary');
            
            if (response.status === 200) {
                const data = response.data;
                console.log('✅ Data summary retrieved');
                console.log('\nSummary:');
                Object.entries(data.summary).forEach(([key, value]) => {
                    console.log(`  ${key}: ${value}`);
                });
                
                console.log('\nTop Cities by Sales:');
                data.cities.slice(0, 3).forEach(city => {
                    console.log(`  ${city.city_name}: ${city.records} records, ₹${city.total_sales}`);
                });
                
            } else {
                console.log(`❌ Data summary failed: ${response.status}`);
            }
            
        } catch (error) {
            console.log('❌ Data summary error:', error.response?.data || error.message);
        }
    }

    async testHierarchyOverview() {
        console.log('\n🔍 Testing Hierarchy Overview...');
        console.log('-'.repeat(40));
        
        try {
            const response = await this.client.get('/api/hierarchy-overview');
            
            if (response.status === 200) {
                const data = response.data;
                console.log('✅ Hierarchy overview retrieved');
                console.log('\nTop Parent SKUs:');
                
                data.parent_sku_overview.slice(0, 5).forEach(parent => {
                    console.log(`  ${parent.parent_sku}:`);
                    console.log(`    Product: ${parent.product_name}`);
                    console.log(`    Children: ${parent.child_count}`);
                    console.log(`    Cities: ${parent.city_count}`);
                    console.log(`    Avg Stock: ${parent.avg_stock}`);
                    console.log('');
                });
                
            } else {
                console.log(`❌ Hierarchy overview failed: ${response.status}`);
            }
            
        } catch (error) {
            console.log('❌ Hierarchy overview error:', error.response?.data || error.message);
        }
    }

    async sleep(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    async runAllTests() {
        console.log('🚀 Starting Advanced Stock API Test Suite');
        console.log('='.repeat(60));
        
        const startTime = Date.now();
        
        // Check if server is running
        const healthOK = await this.testHealthCheck();
        if (!healthOK) {
            console.log('\n❌ Server not accessible. Make sure the server is running!');
            console.log('Run: npm start');
            return;
        }
        
        // Run all tests
        await this.testAdvancedStockAPI();
        await this.testPerformanceBenchmark();
        await this.testCacheOperations();
        await this.testDataSummary();
        await this.testHierarchyOverview();
        
        const totalTime = Date.now() - startTime;
        
        console.log('\n' + '='.repeat(60));
        console.log('🎉 All tests completed!');
        console.log(`⏱️  Total time: ${totalTime}ms`);
        console.log('='.repeat(60));
    }
}

// Run tests if called directly
if (require.main === module) {
    const tester = new APITester();
    tester.runAllTests().catch(console.error);
}

module.exports = APITester;
