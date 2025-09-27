"""
Zepto Product Scraper
Scrapes all products from a specific Zepto brand page and saves to CSV
Target URL: https://www.zeptonow.com/brand/Lay's/18d6cb72-65aa-4881-8984-a08aa295dd35
"""

import requests
import csv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time
import re
from urllib.parse import urljoin
import json

class ZeptoScraper:
    def __init__(self, headless=True):
        """Initialize the scraper with Chrome WebDriver"""
        chrome_options = Options()
        if headless:
            chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        self.products = []
        
    def set_location(self, latitude, longitude, city_name="Mumbai"):
        """Set location cookies for multi-city scraping"""
        self.driver.get("https://www.zeptonow.com")
        time.sleep(3)
        
        # Set location cookies
        self.driver.add_cookie({
            'name': 'latitude',
            'value': str(latitude),
            'domain': '.zeptonow.com'
        })
        self.driver.add_cookie({
            'name': 'longitude', 
            'value': str(longitude),
            'domain': '.zeptonow.com'
        })
        
        print(f"Location set to {city_name} ({latitude}, {longitude})")
        time.sleep(2)

    def extract_product_id_from_url(self, url):
        """Extract product ID from product URL"""
        # Look for pvid parameter in URL
        match = re.search(r'/pvid/([a-f0-9-]+)', url)
        if match:
            return match.group(1)
        
        # Fallback to extracting from URL path
        match = re.search(r'/pn/[^/]+/([a-f0-9-]+)', url)
        if match:
            return match.group(1)
            
        return "unknown"

    def scroll_and_load_products(self):
        """Scroll down to load all products via infinite scroll"""
        print("Loading all products...")
        last_height = self.driver.execute_script("return document.body.scrollHeight")
        
        while True:
            # Scroll down to bottom
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            
            # Wait for new content to load
            time.sleep(3)
            
            # Calculate new scroll height
            new_height = self.driver.execute_script("return document.body.scrollHeight")
            
            if new_height == last_height:
                # Try one more scroll to be sure
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)
                final_height = self.driver.execute_script("return document.body.scrollHeight")
                if final_height == new_height:
                    break
            
            last_height = new_height

    def scrape_products(self, brand_url, location_data=None):
        """Scrape all products from the brand page"""
        if location_data:
            self.set_location(location_data['lat'], location_data['lng'], location_data['city'])
        
        print(f"Accessing brand page: {brand_url}")
        self.driver.get(brand_url)
        
        # Wait for page to load
        try:
            WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.TAG_NAME, "a"))
            )
        except TimeoutException:
            print("Page load timeout")
            return []
        
        time.sleep(5)
        
        # Load all products
        self.scroll_and_load_products()
        
        # Find all product links
        product_elements = self.driver.find_elements(By.XPATH, "//a[contains(@href, '/pn/')]")
        
        print(f"Found {len(product_elements)} product links")
        
        for index, element in enumerate(product_elements, 1):
            try:
                product_data = self.extract_product_data(element, index)
                if product_data:
                    self.products.append(product_data)
                    print(f"Scraped product {index}: {product_data['product_name']}")
            except Exception as e:
                print(f"Error scraping product {index}: {str(e)}")
                continue
        
        return self.products

    def extract_product_data(self, product_element, position):
        """Extract data from a single product element"""
        try:
            # Get product URL and ID
            product_url = product_element.get_attribute('href')
            product_id = self.extract_product_id_from_url(product_url)
            
            # Extract product name
            name_elements = product_element.find_elements(By.XPATH, ".//h3 | .//h4 | .//*[contains(@class, 'product') and contains(@class, 'name')] | .//*[contains(text(), \"Lay's\")]")
            product_name = "Unknown Product"
            for elem in name_elements:
                text = elem.text.strip()
                if text and len(text) > 3:
                    product_name = text
                    break
            
            # Extract image URL
            img_elements = product_element.find_elements(By.TAG_NAME, "img")
            image_url = ""
            for img in img_elements:
                src = img.get_attribute('src')
                if src and ('jpg' in src or 'png' in src or 'webp' in src):
                    image_url = src
                    break
            
            # Extract prices
            price_elements = product_element.find_elements(By.XPATH, ".//*[contains(text(), '₹')]")
            mrp = 0
            selling_price = 0
            
            prices = []
            for price_elem in price_elements:
                text = price_elem.text.strip()
                price_match = re.findall(r'₹(\d+)', text)
                for price in price_match:
                    prices.append(int(price))
            
            # Sort prices to get MRP (highest) and selling price (lowest)
            if prices:
                prices.sort()
                selling_price = prices[0]
                mrp = prices[-1] if len(prices) > 1 else selling_price
            
            # Check stock availability
            stock_available = True
            out_of_stock_indicators = ['out of stock', 'sold out', 'unavailable', 'coming soon']
            element_text = product_element.text.lower()
            for indicator in out_of_stock_indicators:
                if indicator in element_text:
                    stock_available = False
                    break
            
            # Check if sponsored (look for ad indicators)
            sponsored = False
            ad_indicators = ['sponsored', 'ad', 'promoted']
            for indicator in ad_indicators:
                if indicator in element_text.lower():
                    sponsored = True
                    break
            
            return {
                'product_name': product_name,
                'product_image_url': image_url,
                'product_id': product_id,
                'stock_availability': stock_available,
                'sponsored': sponsored,
                'mrp': mrp,
                'selling_price': selling_price,
                'product_position': position
            }
            
        except Exception as e:
            print(f"Error extracting product data: {str(e)}")
            return None

    def save_to_csv(self, filename="products.csv"):
        """Save scraped products to CSV file"""
        if not self.products:
            print("No products to save")
            return
        
        fieldnames = [
            'product_name',
            'product_image_url', 
            'product_id',
            'stock_availability',
            'sponsored',
            'mrp',
            'selling_price',
            'product_position'
        ]
        
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(self.products)
        
        print(f"Saved {len(self.products)} products to {filename}")

    def close(self):
        """Close the webdriver"""
        if self.driver:
            self.driver.quit()

def main():
    """Main function to run the scraper"""
    # Brand URL for Lay's
    brand_url = "https://www.zeptonow.com/brand/Lay's/18d6cb72-65aa-4881-8984-a08aa295dd35"
    
    # Top cities coordinates for multi-location scraping (optional)
    cities = [
        {'city': 'Mumbai', 'lat': 19.0760, 'lng': 72.8777},
        {'city': 'Delhi', 'lat': 28.7041, 'lng': 77.1025},
        {'city': 'Bangalore', 'lat': 12.9716, 'lng': 77.5946},
        {'city': 'Hyderabad', 'lat': 17.3850, 'lng': 78.4867},
        {'city': 'Chennai', 'lat': 13.0827, 'lng': 80.2707}
    ]
    
    scraper = ZeptoScraper(headless=False)  # Set to True for headless mode
    
    try:
        # Simple single location scraping
        print("Starting product scraping...")
        products = scraper.scrape_products(brand_url)
        
        # Optional: Multi-location scraping
        # Uncomment below to scrape for multiple cities
        all_products = []
        for city_data in cities:
            print(f"\n--- Scraping for {city_data['city']} ---")
            city_products = scraper.scrape_products(brand_url, city_data)
            for product in city_products:
                product['location'] = city_data['city']
            all_products.extend(city_products)
        
        scraper.products = all_products
        
        scraper.save_to_csv("products.csv")
        
    except Exception as e:
        print(f"Error during scraping: {str(e)}")
    finally:
        scraper.close()

if __name__ == "__main__":
    main()
