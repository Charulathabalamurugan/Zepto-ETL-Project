"""
Download real stock data from Google Sheets
"""

import pandas as pd
import requests

def download_stock_csv():
    """Download stock data from Google Sheets"""
    
    # Convert Google Sheets URL to CSV export URL
    sheet_id = "10lOoozWOf1paFpPTxUfx-cuqxXjbsmFh_DOr9mUAP3U"
    gid = "248630542"
    csv_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid}"
    
    print("Downloading real stock data from Google Sheets...")
    
    try:
        # Download the CSV
        response = requests.get(csv_url)
        response.raise_for_status()
        
        # Save to file
        with open('stock_data_real.csv', 'wb') as f:
            f.write(response.content)
        
        print("Downloaded successfully as 'stock_data_real.csv'")
        
        # Load and examine the data
        df = pd.read_csv('stock_data_real.csv')
        
        print(f"\nREAL STOCK DATA ANALYSIS:")
        print(f"   Rows: {len(df)}")
        print(f"   Columns: {df.columns.tolist()}")
        
        print(f"\nDATA SUMMARY:")
        print(f"   Cities: {df['city_name'].nunique()} - {df['city_name'].unique()}")
        print(f"   Products: {df['product_id'].nunique()}")
        print(f"   Date range: {df['date'].min()} to {df['date'].max()}")
        print(f"   Categories: {df['category'].nunique()} - {df['category'].unique()[:5]}")
        
        print(f"\nSAMPLE DATA:")
        print(df.head(3).to_string(index=False))
        
        return df
        
    except Exception as e:
        print(f"❌ Error downloading data: {e}")
        return None

if __name__ == '__main__':
    download_stock_csv()
