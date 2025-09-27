# 🚀 Advanced Stock API - Node.js Implementation

A high-performance Node.js API for stock availability with parent-child SKU hierarchy, caching, and performance optimization.

## 📋 Features

### 🎯 Core Features
- **Parent-Child SKU Hierarchy**: Automatic aggregation of child metrics to parent SKUs
- **Performance Optimization**: Database indexing, WAL mode, query optimization
- **In-Memory Caching**: 5-minute TTL with cache statistics and management
- **Real Stock Data**: Integration with Google Sheets data (1,300+ records)
- **Multi-City Support**: Delhi, Mumbai, Bangalore, Chennai, Hyderabad

### 🔧 Technical Features
- **Express.js**: Fast, unopinionated web framework
- **SQLite3**: Embedded database with performance optimizations
- **Node-Cache**: In-memory caching layer
- **Security**: Helmet.js security headers
- **Compression**: Gzip response compression
- **Performance Benchmarking**: Built-in performance testing

## 🛠️ Installation

### Prerequisites
- Node.js 16+ 
- npm or yarn

### Quick Setup
```bash
# Install dependencies
npm install

# Set up database with real stock data
npm run setup

# Start the server
npm start

# Or run in development mode
npm run dev
```

## 📊 API Endpoints

### Stock Availability API
**POST** `/api/stock-availability-advanced`

**Request Body:**
```json
{
  "city": "Delhi",
  "skus": ["SKU1", "SKU2"],
  "page": 1,
  "pageSize": 10,
  "sortBy": "SKU",
  "sortOrder": "ASC",
  "search": "Baby Wipes"
}
```

**Response Format:**
```json
{
  "city": "Delhi",
  "data": [
    {
      "sku": "SKU1",
      "instock_darkstores": 120,
      "total_darkstores": 250,
      "instock_darkstores_percentage": 48.0,
      "total_stock": 240,
      "days_of_stock": 2.25,
      "out_of_stock_flag": false,
      "children": [
        {
          "sku": "SKU-A1",
          "instock_darkstores": 100,
          "out_of_stock_darkstores": 20,
          "total_darkstores": 120,
          "instock_darkstores_percentage": 83.33,
          "total_stock": 100,
          "days_of_stock": 2.0,
          "out_of_stock_flag": false
        }
      ]
    }
  ],
  "performance": {
    "execution_time_ms": 45,
    "cache_used": false,
    "total_results": 1
  }
}
```

### Performance & Analytics Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/performance-benchmark` | GET | Performance testing with cache comparison |
| `/api/cache-stats` | GET | Cache statistics and key information |
| `/api/clear-cache` | POST | Clear all cached responses |
| `/api/data-summary` | GET | Overall data summary and city breakdown |
| `/api/hierarchy-overview` | GET | Parent-child SKU hierarchy overview |
| `/api/health-advanced` | GET | Health check with feature list |

## 🧪 Testing

### Run All Tests
```bash
npm test
```

### Run Performance Benchmark
```bash
npm run benchmark
```

### Manual Testing Examples

**Test Parent-Child Hierarchy:**
```bash
curl -X POST http://localhost:5000/api/stock-availability-advanced \
  -H "Content-Type: application/json" \
  -d '{"city": "Delhi", "pageSize": 2}'
```

**Test Performance Benchmark:**
```bash
curl http://localhost:5000/api/performance-benchmark
```

**Test Cache Operations:**
```bash
# Get cache stats
curl http://localhost:5000/api/cache-stats

# Clear cache
curl -X POST http://localhost:5000/api/clear-cache
```

## 📈 Performance Metrics

### Database Optimization
- **Indexes**: 8 strategic indexes on frequently queried columns
- **WAL Mode**: Write-Ahead Logging for better concurrent performance  
- **Cache Size**: 10,000 pages in memory
- **Aggregation Cache**: Pre-calculated parent SKU metrics

### Typical Response Times
- **Cold Cache**: 25-80ms (first request)
- **Warm Cache**: 1-5ms (subsequent requests) 
- **Performance Improvement**: 80-95% with caching

### Data Scale
- **Parent SKUs**: 10 (SKU1-SKU10)
- **Child SKUs**: 24 (SKU-A1, SKU-A2, etc.)
- **Total Records**: 3,120+ across 5 cities
- **Database Size**: ~500KB optimized

## 🏗️ Architecture

### Database Schema
```sql
-- Main stock table with parent-child relationship
stock_data_optimized (
    parent_sku,      -- Parent SKU identifier
    child_sku,       -- Child SKU identifier  
    city_name,       -- City location
    stock_quantity,  -- Available inventory
    instock_darkstores,    -- Stores with stock
    oos_darkstores,        -- Out-of-stock stores
    total_darkstores,      -- Total stores
    -- ... additional metrics
)

-- Aggregation cache for performance
parent_sku_cache (
    city_name,
    parent_sku,
    avg_instock_darkstores,   -- Averaged from children
    sum_total_stock,          -- Summed from children
    child_count,              -- Number of children
    -- ... calculated metrics
)
```

### Parent-Child Aggregation Logic
```javascript
// Parent Metrics Calculation:
instock_darkstores = AVG(child.instock_darkstores)
total_darkstores = AVG(child.total_darkstores)  
instock_darkstores_percentage = parent_instock ÷ parent_total × 100
total_stock = SUM(child.total_stock)
days_of_stock = parent_total_stock ÷ AVG(daily_sales)
out_of_stock_flag = ALL children have total_stock = 0
```

## 🔧 Configuration

### Environment Variables
```bash
PORT=5000                    # Server port
NODE_ENV=production          # Environment mode
CACHE_TTL=300               # Cache TTL in seconds
DB_PATH=./stock_data.db     # Database file path
```

### Performance Tuning
```javascript
// SQLite Configuration
PRAGMA journal_mode = WAL;   // Write-Ahead Logging
PRAGMA synchronous = NORMAL; // Balanced safety/speed
PRAGMA cache_size = 10000;   // 10K pages in memory
PRAGMA temp_store = MEMORY;  // Temp tables in RAM
```

## 🚨 Error Handling

The API includes comprehensive error handling:
- **400**: Bad request parameters
- **404**: Endpoint not found  
- **500**: Internal server error
- **Timeout**: 30-second request timeout

Example error response:
```json
{
  "error": "Invalid parent SKU",
  "message": "SKU not found in database",
  "timestamp": "2025-01-01T12:00:00.000Z"
}
```

## 🔍 Monitoring & Debugging

### Built-in Logging
- Request logging with timestamp
- Performance timing for all queries
- Cache hit/miss statistics
- Error tracking with stack traces

### Performance Monitoring
```javascript
// Check performance stats
GET /api/performance-benchmark

// Monitor cache efficiency  
GET /api/cache-stats

// View data distribution
GET /api/data-summary
```

## 🎯 Business Use Cases

### Inventory Management
- Track stock levels across multiple cities
- Monitor store availability percentages
- Identify low-stock products requiring reorder

### Supply Chain Optimization  
- Analyze days-of-stock remaining
- Compare performance across cities
- Optimize distribution based on sales velocity

### Analytics & Reporting
- Parent-child product performance
- City-wise sales analysis  
- Stock availability trends

## 📦 Project Structure
```
zepto-etl-assignment/
├── package.json              # Dependencies & scripts
├── server.js                 # Main Express server
├── database/
│   ├── config.js            # Database connection & setup
│   └── setup.js             # Data loading & hierarchy creation
├── test/
│   └── api-test.js          # Comprehensive test suite
├── stock_data_real.csv      # Downloaded real data
├── stock_data_optimized_node.db # SQLite database
└── README_NODEJS.md         # This file
```

## 🎉 Getting Started

1. **Install & Setup:**
   ```bash
   npm install
   npm run setup
   ```

2. **Start Server:**
   ```bash
   npm start
   ```

3. **Test API:**
   ```bash
   npm test
   ```

4. **View Performance:**
   ```bash
   curl http://localhost:5000/api/performance-benchmark
   ```

The API will be available at `http://localhost:5000` with full parent-child hierarchy support, caching, and performance optimization! 🚀
