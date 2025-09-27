"""
Test script for Real Stock Availability API
Tests with actual data from Google Sheets
"""

import requests
import json
import time

API_BASE = "http://localhost:5000"

def test_real_stock_api():
    """Test the real stock API with various scenarios"""
    
    print("TESTING REAL STOCK AVAILABILITY API")
    print("=" * 60)
    
    test_cases = [
        {
            "name": "Test 1: Get stock for Chennai",
            "payload": {
                "city": "Chennai",
                "page": 1,
                "pageSize": 3,
                "search": ""
            }
        },
        {
            "name": "Test 2: Search for baby wipes products",
            "payload": {
                "city": "Mumbai", 
                "page": 1,
                "pageSize": 3,
                "search": "wipes"
            }
        },
        {
            "name": "Test 3: Get specific SKUs across cities",
            "payload": {
                "skus": ["SKU1", "SKU2", "SKU3"],
                "page": 1,
                "pageSize": 5,
                "sortBy": "TOTAL STOCK",
                "sortOrder": "DESC"
            }
        },
        {
            "name": "Test 4: Filter by category (Oral & Nasal Care)",
            "payload": {
                "city": "Delhi",
                "page": 1,
                "pageSize": 3,
                "search": "Oral"
            }
        },
        {
            "name": "Test 5: All Delhi products sorted by stock",
            "payload": {
                "city": "Delhi",
                "page": 1,
                "pageSize": 5,
                "sortBy": "TOTAL STOCK",
                "sortOrder": "DESC"
            }
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{test_case['name']}")
        print("-" * 40)
        
        try:
            response = requests.post(
                f"{API_BASE}/api/stock-availability",
                json=test_case['payload'],
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"Success! City: {data.get('city', 'All')}, Records: {len(data.get('data', []))}")
                
                # Show sample records
                if data.get('data'):
                    print("Sample records:")
                    for j, record in enumerate(data['data'][:2], 1):
                        print(f"  {j}. SKU: {record.get('sku', 'N/A')}")
                        print(f"     Stock: {record.get('total_stock', 0)}")
                        print(f"     Instock %: {record.get('instock_darkstores_percentage', 0)}%")
                        print(f"     Days remaining: {record.get('days_of_stock', 0)}")
                        print(f"     Out of stock: {record.get('out_of_stock_flag', False)}")
                
            else:
                print(f"Failed: {response.status_code} - {response.text}")
                
        except requests.exceptions.RequestException as e:
            print(f"Request failed: {str(e)}")
        
        time.sleep(0.5)

def test_summary_endpoint():
    """Test the data summary endpoint"""
    print("\n" + "=" * 60)
    print("TESTING SUMMARY ENDPOINT")
    print("=" * 60)
    
    try:
        response = requests.get(f"{API_BASE}/api/real-stock-summary", timeout=10)
        if response.status_code == 200:
            data = response.json()
            
            print("DATA SUMMARY:")
            summary = data.get('summary', {})
            for key, value in summary.items():
                print(f"  {key.replace('_', ' ').title()}: {value}")
            
            print(f"\nCITY BREAKDOWN:")
            cities = data.get('cities', [])
            for city in cities:
                print(f"  {city['city'].title()}: {city['records']} records, "
                      f"Avg Stock: {city['avg_stock']}, Total Sales: ₹{city['total_sales']}")
        else:
            print(f"Failed: {response.status_code}")
    except Exception as e:
        print(f"Error: {str(e)}")

def compare_with_requirements():
    """Test API response format against requirements"""
    print("\n" + "=" * 60)
    print("VALIDATING API RESPONSE FORMAT")
    print("=" * 60)
    
    # Test specific format matching requirements
    test_payload = {
        "city": "Delhi",
        "skus": ["SKU1", "SKU2"],
        "page": 1,
        "pageSize": 2,
        "sortBy": "TOTAL STOCK", 
        "sortOrder": "DESC",
        "search": "Baby"
    }
    
    try:
        response = requests.post(
            f"{API_BASE}/api/stock-availability",
            json=test_payload,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            
            # Validate response structure
            required_fields = ['city', 'data']
            print("Response Structure Validation:")
            for field in required_fields:
                if field in data:
                    print(f"  ✓ Has '{field}' field")
                else:
                    print(f"  ✗ Missing '{field}' field")
            
            # Validate record structure
            if data.get('data'):
                record = data['data'][0]
                required_record_fields = [
                    'sku', 'instock_darkstores', 'instock_darkstores_percentage',
                    'total_darkstores', 'total_stock', 'days_of_stock', 'out_of_stock_flag'
                ]
                
                print(f"\nRecord Structure Validation:")
                for field in required_record_fields:
                    if field in record:
                        print(f"  ✓ Has '{field}': {record[field]}")
                    else:
                        print(f"  ✗ Missing '{field}'")
                
                print(f"\nSample API Response (matches requirements):")
                print(json.dumps(data, indent=2))
        
    except Exception as e:
        print(f"Validation error: {str(e)}")

if __name__ == "__main__":
    print("Starting Real Stock API Testing...")
    print("Make sure real_stock_api.py is running on port 5000")
    print("Waiting 3 seconds...")
    time.sleep(3)
    
    # Test health endpoint
    try:
        response = requests.get(f"{API_BASE}/api/health", timeout=5)
        if response.status_code == 200:
            health_data = response.json()
            print(f"✓ API is running - Data source: {health_data.get('data_source')}")
        else:
            print("✗ Health check failed")
    except:
        print("✗ Cannot connect to API. Start real_stock_api.py first!")
        exit(1)
    
    # Run tests
    test_real_stock_api()
    test_summary_endpoint() 
    compare_with_requirements()
    
    print("\n" + "=" * 60)
    print("ALL TESTS COMPLETED!")
