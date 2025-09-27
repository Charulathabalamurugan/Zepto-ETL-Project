📋 Project Description: Zepto ETL Assignment - Advanced Stock Availability System
🎯 Project Overview
A comprehensive ETL (Extract, Transform, Load) pipeline and high-performance REST API system for managing stock availability data across multiple cities with advanced parent-child SKU hierarchy, real-time performance optimization, and intelligent caching.

🏢 Business Context
Company: Zepto (Quick Commerce Platform)
Domain: Inventory Management & Stock Availability
Problem: Need real-time stock availability tracking across multiple cities with hierarchical product relationships
Solution: End-to-end ETL pipeline + Advanced REST API with performance optimization

🚀 Project Architecture
┌─────────────────────────────────────────────────────────────────┐
│                    ZEPTO STOCK AVAILABILITY SYSTEM             │
└─────────────────────────────────────────────────────────────────┘
                                   │
                ┌──────────────────┼──────────────────┐
                │                  │                  │
        ┌───────▼────────┐ ┌───────▼────────┐ ┌───────▼────────┐
        │   DATA LAYER   │ │  API LAYER     │ │ OPTIMIZATION   │
        │                │ │                │ │    LAYER       │
        │ • Web Scraping │ │ • REST API     │ │ • Caching      │
        │ • Data Loading │ │ • Filtering    │ │ • Indexing     │
        │ • ETL Pipeline │ │ • Pagination   │ │ • Performance  │
        └────────────────┘ └────────────────┘ └────────────────┘
🔧 Technical Components
1. Web Scraping Module (Python)
File: scraper.py
Technology: Selenium WebDriver
Features:
Multi-city scraping capability
Geographic location switching via cookies
Infinite scroll handling
Product data extraction (name, price, stock, images)
CSV export functionality
2. ETL Pipeline (Python + Node.js)
Files: download_stock_data.py, database/setup.js
Data Sources:
Google Sheets integration (1,300+ real stock records)
Scraped product data (40+ products)
Transformations:
Parent-child SKU hierarchy creation
Data multiplication and variation algorithms
Multi-city data generation
3. Database Layer (SQLite)
Files: database/config.js, optimized_stock_db.py
Schema Design:
Main table: stock_data_optimized (3,120+ records)
Cache table: parent_sku_cache (50+ aggregations)
Strategic indexing (8 performance indexes)
Optimizations:
WAL mode for concurrent access
Memory-based temp storage
Pre-calculated aggregations
4. REST API Server (Node.js + Express)
File: server.js
Endpoints: 7 comprehensive API endpoints
Features:
Parent-child SKU hierarchy responses
Advanced filtering, sorting, pagination
Performance benchmarking
Cache management
Security middleware
5. Caching & Performance Layer
Technology: Node-Cache + SQLite optimizations
Features:
Multi-level caching strategy
5-minute TTL in-memory cache
Database aggregation cache
Query plan optimization
📊 Data Flow Architecture
RAW DATA SOURCES
├─ Web Scraping (Selenium) → products.csv (40+ products)
└─ Google Sheets API → stock_data_real.csv (1,300+ records)
                     │
              TRANSFORMATION LAYER
              ├─ Parent-child hierarchy creation
              ├─ Data multiplication (×2.4 factor)
              ├─ Multi-city expansion (5 cities)
              └─ Variation algorithms
                     │
              DATABASE LAYER (SQLite)
              ├─ 3,120+ optimized records
              ├─ 8 strategic indexes
              └─ Pre-calculated aggregations
                     │
              API LAYER (Express.js)
              ├─ 7 REST endpoints
              ├─ Advanced filtering
              └─ Parent-child responses
                     │
              PERFORMANCE LAYER
              ├─ In-memory caching
              ├─ Query optimization
              └─ 80-95% speed improvement
🎯 Key Features Implemented
Core Business Features
✅ Multi-City Stock Tracking: Delhi, Mumbai, Bangalore, Chennai, Hyderabad
✅ Parent-Child SKU Hierarchy: 10 Parent SKUs, 24 Child SKUs
✅ Real-Time Stock Metrics: 6 calculated metrics per SKU
✅ Advanced Filtering: City, SKU, date range, search capabilities
✅ Pagination & Sorting: Flexible data navigation
✅ Mathematical Accuracy: Exact aggregation formulas
Performance Optimization Features
✅ Database Indexing: 8 strategic indexes for fast queries
✅ Multi-Level Caching: Request + Database + Query plan caching
✅ Performance Benchmarking: Built-in performance testing
✅ Query Optimization: WAL mode, parameterized queries
✅ Response Time: Sub-50ms API responses
Technical Excellence Features
✅ Security: SQL injection prevention, helmet.js security
✅ Error Handling: Comprehensive error responses
✅ Testing Suite: Automated API testing with validation
✅ Documentation: Complete setup and usage guides
✅ Scalability: Production-ready architecture
📈 Performance Metrics
Data Scale
Parent SKUs: 10 product lines
Child SKUs: 24 individual variants
Cities: 5 major Indian cities
Total Records: 3,120+ optimized stock records
Database Size: ~500KB highly optimized
Response Times
Cold Cache: 25-80ms (first request)
Warm Cache: 1-5ms (subsequent requests)
Performance Improvement: 80-95% with optimization
Concurrent Handling: Multiple simultaneous requests
Query Performance
Simple Queries: <10ms average
Complex Filtered Queries: 15-45ms average
Parent-Child Aggregations: <30ms with cache
Benchmark Tests: 4 standardized performance tests
