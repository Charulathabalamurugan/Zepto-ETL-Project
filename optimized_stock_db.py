"""
Advanced Stock Database with Parent-Child SKU Hierarchy and Performance Optimization
"""

import sqlite3
import pandas as pd
import random
from datetime import datetime, timedelta

DATABASE_OPTIMIZED = 'stock_data_optimized.db'

def create_optimized_database():
    """Create optimized database with parent-child SKUs and indexing"""
    
    conn = sqlite3.connect(DATABASE_OPTIMIZED)
    
    # Create main stock table with parent-child relationship
    conn.execute('''
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
    ''')
    
    # Create performance indexes
    conn.execute('CREATE INDEX IF NOT EXISTS idx_city_name ON stock_data_optimized(city_name)')
    conn.execute('CREATE INDEX IF NOT EXISTS idx_parent_sku ON stock_data_optimized(parent_sku)')
    conn.execute('CREATE INDEX IF NOT EXISTS idx_child_sku ON stock_data_optimized(child_sku)')
    conn.execute('CREATE INDEX IF NOT EXISTS idx_date ON stock_data_optimized(date)')
    conn.execute('CREATE INDEX IF NOT EXISTS idx_category ON stock_data_optimized(category)')
    conn.execute('CREATE INDEX IF NOT EXISTS idx_city_parent ON stock_data_optimized(city_name, parent_sku)')
    conn.execute('CREATE INDEX IF NOT EXISTS idx_stock_quantity ON stock_data_optimized(stock_quantity)')
    
    # Create aggregation cache table for better performance
    conn.execute('''
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
    ''')
    
    conn.execute('CREATE INDEX IF NOT EXISTS idx_cache_city_parent ON parent_sku_cache(city_name, parent_sku)')
    
    conn.commit()
    print("Optimized database with indexing created")
    conn.close()

def create_parent_child_hierarchy():
    """Transform real data into parent-child SKU hierarchy"""
    
    if not pd.io.common.file_exists('stock_data_real.csv'):
        print("Error: stock_data_real.csv not found. Run download_stock_data.py first!")
        return
    
    # Load real data
    df = pd.read_csv('stock_data_real.csv')
    
    # Create parent-child mapping based on product categories and names
    parent_child_map = {
        'SKU1': ['SKU-A1', 'SKU-A2', 'SKU-A3'],  # Baby Wipes with Lid
        'SKU2': ['SKU-B1', 'SKU-B2'],             # Baby Wipes with Aloe Vera  
        'SKU3': ['SKU-C1', 'SKU-C2'],             # Another product type
        'SKU4': ['SKU-D1', 'SKU-D2', 'SKU-D3'],  # Tooth & Gum Cleaning
        'SKU5': ['SKU-E1', 'SKU-E2'],             # Nail Clipper
        'SKU6': ['SKU-F1', 'SKU-F2'],             # Another product
        'SKU7': ['SKU-G1', 'SKU-G2', 'SKU-G3'],  # Baby Bottle & Nipple Brush
        'SKU8': ['SKU-H1', 'SKU-H2'],             # Gentle Wet Baby Wipes
        'SKU9': ['SKU-I1', 'SKU-I2'],             # Another product
        'SKU10': ['SKU-J1', 'SKU-J2', 'SKU-J3']  # Final product
    }
    
    # Create parent names mapping
    parent_names = {
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
    }
    
    create_optimized_database()
    conn = sqlite3.connect(DATABASE_OPTIMIZED)
    
    optimized_records = []
    
    for _, row in df.iterrows():
        original_sku = row['product_id']
        
        if original_sku in parent_child_map:
            parent_sku = original_sku
            children = parent_child_map[original_sku]
            
            # Create child records with variations
            for i, child_sku in enumerate(children):
                # Add variations to make children different
                variation_factor = (i + 1) * 0.7  # Different multiplier for each child
                
                child_record = {
                    'date': row['date'],
                    'city_name': row['city_name'].lower(),
                    'parent_sku': parent_sku,
                    'child_sku': child_sku,
                    'product_name': parent_names.get(parent_sku, row['product_name']),
                    'category': row['category'],
                    'total_orders': max(1, int(row['total_orders'] * variation_factor)),
                    'total_sales': row['total_sales'] * variation_factor,
                    'stock_quantity': max(0, int(row['stock_quantity'] * variation_factor)),
                    'instock_darkstores': max(1, int(row['instock_darkstores'] * variation_factor)),
                    'oos_darkstores': max(1, int(row['OOS_darkstores'] * variation_factor)),
                    'total_darkstores': int(row['total_darkstores'] * variation_factor),
                    'average_daily_sales': row['total_orders'] / 26  # Spread over 26 days
                }
                
                optimized_records.append(child_record)
    
    # Insert optimized records
    insert_query = '''
        INSERT INTO stock_data_optimized 
        (date, city_name, parent_sku, child_sku, product_name, category, 
         total_orders, total_sales, stock_quantity, instock_darkstores, 
         oos_darkstores, total_darkstores, average_daily_sales)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    '''
    
    conn.executemany(insert_query, [
        (r['date'], r['city_name'], r['parent_sku'], r['child_sku'], r['product_name'],
         r['category'], r['total_orders'], r['total_sales'], r['stock_quantity'],
         r['instock_darkstores'], r['oos_darkstores'], r['total_darkstores'], 
         r['average_daily_sales']) for r in optimized_records
    ])
    
    conn.commit()
    
    # Verify data
    cursor = conn.execute("SELECT COUNT(*) as count FROM stock_data_optimized")
    count = cursor.fetchone()[0]
    
    print(f"Created {count} child SKU records from {len(df)} original records")
    
    # Show sample hierarchy
    cursor = conn.execute("""
        SELECT parent_sku, child_sku, city_name, stock_quantity 
        FROM stock_data_optimized 
        WHERE parent_sku = 'SKU1' AND city_name = 'delhi' 
        LIMIT 5
    """)
    samples = cursor.fetchall()
    
    print(f"\nSample Parent-Child Hierarchy:")
    current_parent = None
    for sample in samples:
        if sample[0] != current_parent:
            print(f"  Parent: {sample[0]}")
            current_parent = sample[0]
        print(f"    Child: {sample[1]} | City: {sample[2]} | Stock: {sample[3]}")
    
    conn.close()

def build_parent_cache():
    """Pre-calculate parent SKU aggregations for performance"""
    
    conn = sqlite3.connect(DATABASE_OPTIMIZED)
    
    print("Building parent SKU aggregation cache...")
    
    # Clear existing cache
    conn.execute("DELETE FROM parent_sku_cache")
    
    # Calculate parent aggregations
    aggregation_query = '''
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
    '''
    
    conn.execute(aggregation_query)
    conn.commit()
    
    # Verify cache
    cursor = conn.execute("SELECT COUNT(*) FROM parent_sku_cache")
    cache_count = cursor.fetchone()[0]
    
    print(f"Built aggregation cache with {cache_count} parent SKU entries")
    
    conn.close()

def analyze_optimized_data():
    """Analyze the optimized data structure"""
    
    conn = sqlite3.connect(DATABASE_OPTIMIZED)
    
    print(f"\nOPTIMIZED DATA ANALYSIS:")
    print("=" * 50)
    
    # Overall stats
    stats = pd.read_sql_query('''
        SELECT 
            COUNT(DISTINCT parent_sku) as parent_skus,
            COUNT(DISTINCT child_sku) as child_skus,
            COUNT(DISTINCT city_name) as cities,
            COUNT(*) as total_records
        FROM stock_data_optimized
    ''', conn)
    
    print(f"Parent SKUs: {stats.iloc[0]['parent_skus']}")
    print(f"Child SKUs: {stats.iloc[0]['child_skus']}")  
    print(f"Cities: {stats.iloc[0]['cities']}")
    print(f"Total Records: {stats.iloc[0]['total_records']}")
    
    # Parent-child distribution
    hierarchy = pd.read_sql_query('''
        SELECT 
            parent_sku, 
            COUNT(DISTINCT child_sku) as children_count,
            AVG(stock_quantity) as avg_stock
        FROM stock_data_optimized
        GROUP BY parent_sku
        ORDER BY children_count DESC
    ''', conn)
    
    print(f"\nParent-Child Distribution:")
    for _, row in hierarchy.iterrows():
        print(f"  {row['parent_sku']}: {row['children_count']} children, avg stock: {row['avg_stock']:.0f}")
    
    conn.close()

if __name__ == '__main__':
    print("Creating Optimized Stock Database with Parent-Child Hierarchy...")
    
    create_parent_child_hierarchy()
    build_parent_cache()
    analyze_optimized_data()
    
    print(f"\nOptimization Complete!")
    print("Database features:")
    print("  - Parent-child SKU hierarchy")
    print("  - Performance indexes") 
    print("  - Aggregation cache")
    print("  - Query optimization ready")
