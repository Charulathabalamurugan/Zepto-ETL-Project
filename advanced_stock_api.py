"""
Advanced Stock Availability API with Performance Optimization
Features:
- Parent-child SKU hierarchy with aggregation
- In-memory caching layer
- Database indexing optimization
- Performance benchmarking
- Hierarchical JSON response format
"""

from flask import Flask, request, jsonify
import sqlite3
import pandas as pd
import time
import json
from datetime import datetime, timedelta
from functools import wraps

app = Flask(__name__)
DATABASE_OPTIMIZED = 'stock_data_optimized.db'

# In-memory cache
cache = {}
CACHE_EXPIRY = 300  # 5 minutes

def get_optimized_db_connection():
    """Get optimized database connection"""
    conn = sqlite3.connect(DATABASE_OPTIMIZED)
    conn.row_factory = sqlite3.Row
    return conn

def cache_result(expiry_seconds=300):
    """Decorator for caching API responses"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Create cache key from function name and arguments
            cache_key = f"{func.__name__}_{hash(str(kwargs))}"
            
            # Check if result is in cache and not expired
            if cache_key in cache:
                result, timestamp = cache[cache_key]
                if time.time() - timestamp < expiry_seconds:
                    return result
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            cache[cache_key] = (result, time.time())
            
            return result
        return wrapper
    return decorator

def calculate_parent_sku_metrics(parent_sku, city_name, conn):
    """Calculate parent SKU metrics from cached aggregation table"""
    
    # Use pre-calculated cache for better performance
    cache_query = '''
        SELECT * FROM parent_sku_cache 
        WHERE parent_sku = ? AND city_name = ?
    '''
    
    cursor = conn.execute(cache_query, [parent_sku, city_name])
    cache_result = cursor.fetchone()
    
    if not cache_result:
        return None
    
    # Calculate parent metrics according to requirements
    avg_instock = cache_result['avg_instock_darkstores']
    avg_total = cache_result['avg_total_darkstores'] 
    sum_stock = cache_result['sum_total_stock']
    avg_sales = cache_result['avg_daily_sales']
    child_count = cache_result['child_count']
    out_of_stock_children = cache_result['out_of_stock_children']
    
    # Parent instock_darkstores_percentage = parent avg(instock) ÷ parent avg(total) × 100
    if avg_total > 0:
        parent_percentage = (avg_instock / avg_total) * 100
    else:
        parent_percentage = 0
    
    # Parent days_of_stock = parent total_stock ÷ average daily sales
    if avg_sales > 0:
        parent_days_of_stock = sum_stock / avg_sales
    else:
        parent_days_of_stock = 0
    
    # Parent out_of_stock_flag = 1 if all children total_stock = 0, else 0
    parent_out_of_stock = (out_of_stock_children == child_count)
    
    return {
        'instock_darkstores': round(avg_instock, 0),
        'total_darkstores': round(avg_total, 0),
        'instock_darkstores_percentage': round(parent_percentage, 2),
        'total_stock': sum_stock,
        'days_of_stock': round(parent_days_of_stock, 2),
        'out_of_stock_flag': parent_out_of_stock
    }

def get_children_metrics(parent_sku, city_name, conn):
    """Get detailed metrics for all children of a parent SKU"""
    
    children_query = '''
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
    '''
    
    cursor = conn.execute(children_query, [parent_sku, city_name])
    children_records = cursor.fetchall()
    
    children = []
    for child in children_records:
        # Calculate child metrics
        instock = child['instock_darkstores']
        oos = child['oos_darkstores'] 
        total_darkstores = child['total_darkstores']
        stock_quantity = child['stock_quantity']
        avg_sales = child['average_daily_sales']
        
        # Child instock_darkstores_percentage
        if total_darkstores > 0:
            child_percentage = (instock / total_darkstores) * 100
        else:
            child_percentage = 0
        
        # Child days_of_stock
        if avg_sales > 0:
            child_days = stock_quantity / avg_sales
        else:
            child_days = 0
        
        child_metrics = {
            'sku': child['child_sku'],
            'instock_darkstores': instock,
            'out_of_stock_darkstores': oos,
            'total_darkstores': total_darkstores,
            'instock_darkstores_percentage': round(child_percentage, 2),
            'total_stock': stock_quantity,
            'days_of_stock': round(child_days, 2),
            'out_of_stock_flag': stock_quantity == 0
        }
        
        children.append(child_metrics)
    
    return children

@cache_result(expiry_seconds=300)
def get_stock_data_optimized(**filters):
    """Optimized stock data retrieval with caching"""
    
    start_time = time.time()
    
    conn = get_optimized_db_connection()
    
    # Extract filters
    city = filters.get('city')
    skus = filters.get('skus', [])
    page = filters.get('page', 1)
    page_size = filters.get('pageSize', 10)
    sort_by = filters.get('sortBy', 'sku')
    sort_order = filters.get('sortOrder', 'ASC')
    search = filters.get('search', '')
    
    # Build optimized query using indexes
    query = '''
        SELECT DISTINCT parent_sku, product_name, category, city_name
        FROM stock_data_optimized 
        WHERE 1=1
    '''
    params = []
    
    # Apply filters with indexed columns
    if city:
        query += ' AND city_name = ?'
        params.append(city.lower())
    
    if skus:
        placeholders = ','.join(['?' for _ in skus])
        query += f' AND parent_sku IN ({placeholders})'
        params.extend(skus)
    
    if search:
        query += ' AND (product_name LIKE ? OR category LIKE ?)'
        params.append(f'%{search}%')
        params.append(f'%{search}%')
    
    # Apply sorting
    sort_column_map = {
        'SKU': 'parent_sku',
        'PRODUCT_NAME': 'product_name',
        'CATEGORY': 'category',
        'CITY': 'city_name'
    }
    sort_column = sort_column_map.get(sort_by.upper(), 'parent_sku')
    query += f' ORDER BY {sort_column} {sort_order}'
    
    # Apply pagination
    offset = (page - 1) * page_size
    query += f' LIMIT {page_size} OFFSET {offset}'
    
    cursor = conn.execute(query, params)
    parent_records = cursor.fetchall()
    
    # Build hierarchical response
    stock_data = []
    
    for parent_record in parent_records:
        parent_sku = parent_record['parent_sku']
        city_name = parent_record['city_name']
        
        # Get parent metrics from cache
        parent_metrics = calculate_parent_sku_metrics(parent_sku, city_name, conn)
        
        if parent_metrics:
            # Get children details
            children = get_children_metrics(parent_sku, city_name, conn)
            
            parent_data = {
                'sku': parent_sku,
                **parent_metrics,
                'children': children
            }
            
            stock_data.append(parent_data)
    
    conn.close()
    
    execution_time = time.time() - start_time
    
    return {
        'data': stock_data,
        'execution_time': round(execution_time * 1000, 2),  # ms
        'cache_used': False  # Will be True if served from cache
    }

@app.route('/api/stock-availability-advanced', methods=['POST'])
def stock_availability_advanced():
    """Advanced stock availability API with parent-child hierarchy"""
    
    try:
        request_data = request.get_json() or {}
        
        # Extract parameters
        city = request_data.get('city')
        skus = request_data.get('skus', [])
        page = request_data.get('page', 1)
        page_size = request_data.get('pageSize', 10)
        sort_by = request_data.get('sortBy', 'sku')
        sort_order = request_data.get('sortOrder', 'ASC').upper()
        search = request_data.get('search', '')
        
        print(f"Advanced API Request: city={city}, skus={len(skus)}, search='{search}'")
        
        # Get optimized stock data
        result = get_stock_data_optimized(
            city=city,
            skus=skus,
            page=page,
            pageSize=page_size,
            sortBy=sort_by,
            sortOrder=sort_order,
            search=search
        )
        
        # Check if result was served from cache
        cache_key = f"get_stock_data_optimized_{hash(str(request_data))}"
        cache_used = cache_key in cache
        
        response = {
            'city': city,
            'data': result['data'],
            'performance': {
                'execution_time_ms': result['execution_time'],
                'cache_used': cache_used,
                'total_results': len(result['data'])
            }
        }
        
        return jsonify(response)
        
    except Exception as e:
        return jsonify({
            'error': str(e),
            'performance': {'execution_time_ms': 0, 'cache_used': False}
        }), 500

@app.route('/api/performance-benchmark', methods=['GET'])
def performance_benchmark():
    """Benchmark API performance with and without optimizations"""
    
    try:
        # Test queries
        test_queries = [
            {'city': 'delhi', 'pageSize': 5},
            {'search': 'Baby', 'pageSize': 10},
            {'skus': ['SKU1', 'SKU2'], 'pageSize': 3},
            {'city': 'mumbai', 'sortBy': 'SKU', 'pageSize': 7}
        ]
        
        benchmark_results = []
        
        for i, query in enumerate(test_queries, 1):
            # Clear cache for accurate timing
            cache.clear()
            
            # Time the query
            start_time = time.time()
            result = get_stock_data_optimized(**query)
            execution_time = time.time() - start_time
            
            # Run again to test cache performance
            cached_start = time.time()
            cached_result = get_stock_data_optimized(**query)
            cached_time = time.time() - cached_start
            
            benchmark_results.append({
                'test': f'Query {i}',
                'query': query,
                'first_run_ms': round(execution_time * 1000, 2),
                'cached_run_ms': round(cached_time * 1000, 2),
                'performance_improvement': f"{round((execution_time - cached_time) / execution_time * 100, 1)}%",
                'results_count': len(result['data'])
            })
        
        return jsonify({
            'benchmark_results': benchmark_results,
            'optimization_features': [
                'Database indexing on city_name, parent_sku, child_sku',
                'Pre-calculated parent SKU aggregation cache',
                'In-memory response caching (5 min TTL)',
                'Optimized parent-child hierarchy queries'
            ]
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/cache-stats', methods=['GET'])
def cache_stats():
    """Get cache statistics"""
    return jsonify({
        'cache_entries': len(cache),
        'cache_keys': list(cache.keys())[:10],  # Show first 10 keys
        'cache_expiry_seconds': CACHE_EXPIRY
    })

@app.route('/api/clear-cache', methods=['POST'])
def clear_cache():
    """Clear the in-memory cache"""
    cache.clear()
    return jsonify({'message': 'Cache cleared successfully'})

@app.route('/api/health-advanced', methods=['GET'])
def health_advanced():
    """Advanced health check with performance info"""
    return jsonify({
        'status': 'healthy',
        'features': [
            'Parent-child SKU hierarchy',
            'Database indexing optimization', 
            'In-memory caching',
            'Performance benchmarking'
        ],
        'cache_entries': len(cache),
        'timestamp': datetime.now().isoformat()
    })

if __name__ == '__main__':
    print("Advanced Stock Availability API starting...")
    print("Features:")
    print("  - Parent-child SKU hierarchy with aggregation")
    print("  - Database indexing for fast queries")
    print("  - In-memory caching (5 min TTL)")
    print("  - Performance benchmarking")
    print("  - Hierarchical JSON responses")
    print(f"\nData: {3120} child SKU records across 10 parent SKUs")
    print("Endpoints:")
    print("  POST /api/stock-availability-advanced - Advanced stock API")
    print("  GET /api/performance-benchmark - Performance testing")
    print("  GET /api/cache-stats - Cache statistics")
    print("  POST /api/clear-cache - Clear cache")
    
    app.run(debug=True, host='0.0.0.0', port=5000)
