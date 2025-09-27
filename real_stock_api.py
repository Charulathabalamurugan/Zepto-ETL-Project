"""
Stock Availability API using Real Stock Data
Updated to work with actual stock data from Google Sheets
"""

from flask import Flask, request, jsonify
import sqlite3
import pandas as pd
from datetime import datetime

app = Flask(__name__)
DATABASE_REAL = 'stock_data_real.db'

def get_real_db_connection():
    """Get database connection for real stock data"""
    conn = sqlite3.connect(DATABASE_REAL)
    conn.row_factory = sqlite3.Row
    return conn

def calculate_real_stock_metrics(records):
    """Calculate stock availability metrics from real data records"""
    
    if not records:
        return []
    
    results = []
    
    for record in records:
        # Extract values from real database record
        instock_darkstores = int(record['instock_darkstores'])
        oos_darkstores = int(record['oos_darkstores']) 
        total_darkstores = int(record['total_darkstores'])
        stock_quantity = int(record['stock_quantity'])
        avg_daily_sales = float(record['average_daily_sales']) if record['average_daily_sales'] else 1.0
        
        # Calculate instock_darkstores_percentage
        if total_darkstores > 0:
            instock_percentage = (instock_darkstores / total_darkstores) * 100
        else:
            instock_percentage = 0
        
        # Calculate days_of_stock
        if avg_daily_sales > 0:
            days_of_stock = stock_quantity / avg_daily_sales
        else:
            days_of_stock = 0
        
        # Calculate out_of_stock_flag
        out_of_stock_flag = stock_quantity == 0
        
        # Build result object matching required API format
        result = {
            "sku": record['product_id'],
            "instock_darkstores": instock_darkstores,
            "instock_darkstores_percentage": round(instock_percentage, 1),
            "total_darkstores": total_darkstores,
            "total_stock": stock_quantity,
            "days_of_stock": round(days_of_stock, 1),
            "out_of_stock_flag": out_of_stock_flag
        }
        
        results.append(result)
    
    return results

@app.route('/api/stock-availability', methods=['POST'])
def stock_availability_real():
    """Stock availability endpoint using real data"""
    try:
        # Get request data
        data = request.get_json() or {}
        
        # Extract parameters with defaults
        city = data.get('city')
        skus = data.get('skus', [])
        page = data.get('page', 1)
        page_size = data.get('pageSize', 10)
        sort_by = data.get('sortBy', 'sku')
        sort_order = data.get('sortOrder', 'ASC').upper()
        date_from = data.get('dateFrom')
        date_to = data.get('dateTo')
        search = data.get('search', '')
        
        print(f"API Request - City: {city}, SKUs: {len(skus)}, Search: '{search}'")
        
        # Build SQL query for real data
        conn = get_real_db_connection()
        query = "SELECT * FROM stock_data_real WHERE 1=1"
        params = []
        
        # Apply filters
        if city:
            # Handle case-insensitive city matching
            query += " AND LOWER(city_name) = LOWER(?)"
            params.append(city)
        
        if skus:
            placeholders = ','.join(['?' for _ in skus])
            query += f" AND product_id IN ({placeholders})"
            params.extend(skus)
        
        if search:
            query += " AND (product_name LIKE ? OR category LIKE ?)"
            params.append(f"%{search}%")
            params.append(f"%{search}%")
        
        if date_from:
            query += " AND date >= ?"
            params.append(date_from)
        
        if date_to:
            query += " AND date <= ?"
            params.append(date_to)
        
        # Apply sorting
        sort_column_map = {
            'TOTAL STOCK': 'stock_quantity',
            'INSTOCK_DARKSTORES': 'instock_darkstores',
            'SKU': 'product_id',
            'CITY': 'city_name',
            'PRODUCT_NAME': 'product_name',
            'CATEGORY': 'category',
            'SALES': 'total_sales'
        }
        
        sort_column = sort_column_map.get(sort_by.upper(), 'product_id')
        query += f" ORDER BY {sort_column} {'ASC' if sort_order == 'ASC' else 'DESC'}"
        
        # Apply pagination
        offset = (page - 1) * page_size
        query += f" LIMIT {page_size} OFFSET {offset}"
        
        print(f"Executing query: {query}")
        
        # Execute query
        cursor = conn.execute(query, params)
        records = cursor.fetchall()
        conn.close()
        
        print(f"Found {len(records)} records")
        
        # Calculate metrics
        stock_data = calculate_real_stock_metrics(records)
        
        # Build response
        response = {
            "city": city,
            "data": stock_data
        }
        
        return jsonify(response)
        
    except Exception as e:
        print(f"API Error: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/real-stock-summary', methods=['GET'])
def real_stock_summary():
    """Get summary of real stock data"""
    try:
        conn = get_real_db_connection()
        
        # Get summary statistics
        summary_query = """
        SELECT 
            COUNT(DISTINCT city_name) as total_cities,
            COUNT(DISTINCT product_id) as total_products,
            COUNT(DISTINCT category) as total_categories,
            COUNT(*) as total_records,
            AVG(stock_quantity) as avg_stock,
            SUM(total_sales) as total_sales,
            MIN(date) as start_date,
            MAX(date) as end_date
        FROM stock_data_real
        """
        
        cursor = conn.execute(summary_query)
        summary = cursor.fetchone()
        
        # Get city breakdown
        city_query = """
        SELECT 
            city_name,
            COUNT(*) as records,
            AVG(stock_quantity) as avg_stock,
            SUM(total_sales) as total_sales
        FROM stock_data_real 
        GROUP BY city_name 
        ORDER BY total_sales DESC
        """
        
        city_cursor = conn.execute(city_query)
        cities = city_cursor.fetchall()
        
        conn.close()
        
        # Build response
        response = {
            "summary": {
                "total_cities": summary['total_cities'],
                "total_products": summary['total_products'], 
                "total_categories": summary['total_categories'],
                "total_records": summary['total_records'],
                "average_stock": round(summary['avg_stock'], 1),
                "total_sales": round(summary['total_sales'], 2),
                "date_range": f"{summary['start_date']} to {summary['end_date']}"
            },
            "cities": [
                {
                    "city": city['city_name'],
                    "records": city['records'],
                    "avg_stock": round(city['avg_stock'], 1),
                    "total_sales": round(city['total_sales'], 2)
                }
                for city in cities
            ]
        }
        
        return jsonify(response)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy", 
        "data_source": "real_stock_data",
        "timestamp": datetime.now().isoformat()
    })

if __name__ == '__main__':
    print("Real Stock Availability API starting...")
    print("Data source: Real stock data from Google Sheets")
    print("Available endpoints:")
    print("  POST /api/stock-availability - Get stock metrics with filters")
    print("  GET /api/real-stock-summary - Get data summary")  
    print("  GET /api/health - Health check")
    print("\nData includes:")
    print("  - 1,300+ real stock records")
    print("  - 5 cities: Chennai, Hyderabad, Mumbai, Bangalore, Delhi")
    print("  - 10 baby care products")
    print("  - 26 days of stock data")
    
    app.run(debug=True, host='0.0.0.0', port=5000)
