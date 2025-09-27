"""
Create database with real stock data structure
"""

import sqlite3
import pandas as pd

DATABASE_REAL = 'stock_data_real.db'

def create_real_stock_database():
    """Create database schema for real stock data"""
    
    conn = sqlite3.connect(DATABASE_REAL)
    
    # Create table with real data structure
    conn.execute('''
        CREATE TABLE IF NOT EXISTS stock_data_real (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            city_name TEXT NOT NULL,
            product_id TEXT NOT NULL,
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
    
    conn.commit()
    print("Real stock database schema created")
    conn.close()

def load_real_stock_data():
    """Load real stock data into database"""
    
    if not pd.io.common.file_exists('stock_data_real.csv'):
        print("Error: stock_data_real.csv not found. Run download_stock_data.py first!")
        return
    
    # Create database
    create_real_stock_database()
    
    # Load CSV
    df = pd.read_csv('stock_data_real.csv')
    
    # Clean column names (handle OOS_darkstores)
    df.columns = df.columns.str.lower().str.replace(' ', '_')
    
    # Calculate average daily sales (total_orders / days in dataset)
    unique_dates = df['date'].nunique()
    df['average_daily_sales'] = df['total_orders'] / max(1, unique_dates)
    
    # Connect to database
    conn = sqlite3.connect(DATABASE_REAL)
    
    # Insert data
    df.to_sql('stock_data_real', conn, if_exists='replace', index=False)
    
    conn.commit()
    
    # Verify data
    cursor = conn.execute("SELECT COUNT(*) as count FROM stock_data_real")
    count = cursor.fetchone()[0]
    print(f"Loaded {count} real stock records into database")
    
    # Show sample
    cursor = conn.execute("SELECT * FROM stock_data_real LIMIT 3")
    samples = cursor.fetchall()
    print(f"\nSample records:")
    for sample in samples[:3]:
        print(f"  {sample[2]} | {sample[4]} | Stock: {sample[8]} | City: {sample[1]}")
    
    conn.close()

def analyze_real_stock_data():
    """Analyze the real stock data"""
    
    conn = sqlite3.connect(DATABASE_REAL)
    
    print("\nREAL STOCK DATA ANALYSIS:")
    print("=" * 50)
    
    # Cities analysis
    cities = pd.read_sql_query(
        "SELECT city_name, COUNT(*) as records, AVG(stock_quantity) as avg_stock FROM stock_data_real GROUP BY city_name ORDER BY city_name", 
        conn
    )
    
    print("Cities:")
    for _, row in cities.iterrows():
        print(f"  {row['city_name'].title()}: {row['records']} records, avg stock: {row['avg_stock']:.0f}")
    
    # Products analysis
    products = pd.read_sql_query(
        "SELECT product_id, product_name, category, COUNT(DISTINCT city_name) as cities, AVG(stock_quantity) as avg_stock FROM stock_data_real GROUP BY product_id ORDER BY avg_stock DESC LIMIT 5", 
        conn
    )
    
    print(f"\nTop products by average stock:")
    for _, row in products.iterrows():
        print(f"  {row['product_id']}: {row['product_name'][:40]}... | Avg Stock: {row['avg_stock']:.0f}")
    
    # Date range
    date_info = pd.read_sql_query(
        "SELECT MIN(date) as start_date, MAX(date) as end_date, COUNT(DISTINCT date) as unique_dates FROM stock_data_real", 
        conn
    )
    
    print(f"\nDate range: {date_info.iloc[0]['start_date']} to {date_info.iloc[0]['end_date']} ({date_info.iloc[0]['unique_dates']} days)")
    
    conn.close()

if __name__ == '__main__':
    print("Setting up real stock data database...")
    load_real_stock_data()
    analyze_real_stock_data()
