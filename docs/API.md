# Profit Tracker AI - API Documentation

## Authentication

All API endpoints require authentication except for the login and registration endpoints. Authentication is handled via session cookies.

### Login
```
POST /login
Content-Type: application/x-www-form-urlencoded

username=your_username&password=your_password
```

### Logout
```
GET /logout
```

## Receipt Management

### Upload Receipt
```
POST /api/upload
Content-Type: multipart/form-data

image: (file)
job_number: JOB123 (optional)
```

**Response:**
```json
{
    "success": true,
    "receipt_id": 123,
    "extracted_data": {
        "vendor_name": "Home Depot",
        "total_amount": 156.78,
        "date": "2024-01-15"
    }
}
```

### Get Receipt
```
GET /api/receipts/{receipt_id}
```

### Update Receipt
```
POST /api/receipts/{receipt_id}/update
Content-Type: application/json

{
    "vendor_name": "Updated Vendor",
    "total_amount": 200.00,
    "job_id": 45
}
```

### Delete Receipt
```
POST /api/receipts/{receipt_id}/delete
```

## Job Management

### List Jobs
```
GET /api/jobs
```

**Query Parameters:**
- `page`: Page number (default: 1)
- `per_page`: Items per page (default: 20)
- `search`: Search term
- `status`: Filter by status

### Create Job
```
POST /api/jobs
Content-Type: application/json

{
    "job_number": "JOB123",
    "customer_name": "John Doe",
    "job_type": "installation",
    "revenue": 1500.00
}
```

### Update Job
```
POST /api/jobs/{job_id}/update
Content-Type: application/json

{
    "status": "completed",
    "revenue": 1600.00
}
```

## Analytics & Insights

### Profit Trends
```
GET /api/insights/trends

Query Parameters:
- days: Number of days to analyze (default: 30)
```

**Response:**
```json
{
    "trends": [
        {
            "date": "2024-01-15",
            "revenue": 5000.00,
            "expenses": 3000.00,
            "profit": 2000.00
        }
    ],
    "summary": {
        "total_revenue": 150000.00,
        "total_expenses": 90000.00,
        "total_profit": 60000.00,
        "profit_margin": 40.0
    }
}
```

### Job Pattern Analysis
```
GET /api/insights/patterns
```

**Response:**
```json
{
    "by_job_type": {
        "installation": {
            "count": 50,
            "avg_profit_margin": 45.0,
            "total_profit": 30000.00
        },
        "repair": {
            "count": 100,
            "avg_profit_margin": -5.0,
            "total_profit": -5000.00
        }
    },
    "by_customer": { ... },
    "by_time_period": { ... }
}
```

### Price Recommendations
```
GET /api/insights/recommendations
```

**Response:**
```json
{
    "recommendations": [
        {
            "job_type": "repair",
            "current_avg_revenue": 500.00,
            "recommended_increase": 150.00,
            "reason": "Currently unprofitable with -5% margin"
        }
    ]
}
```

## SMS Integration

### Receive SMS (Webhook)
```
POST /sms/receive
Content-Type: application/x-www-form-urlencoded

From=+1234567890&
To=+0987654321&
Body=Job #JOB123&
MessageSid=SM123&
NumMedia=1&
MediaUrl0=https://api.twilio.com/...&
MediaContentType0=image/jpeg
```

This endpoint is called by Twilio when an SMS/MMS is received.

## Export Functions

### Export Data
```
GET /api/export/{format}

Formats: csv, pdf, json
Query Parameters:
- start_date: YYYY-MM-DD
- end_date: YYYY-MM-DD
- type: receipts|jobs|insights
```

### Bulk Export
```
POST /api/export/bulk

{
    "include_receipts": true,
    "include_jobs": true,
    "include_insights": true,
    "format": "zip"
}
```

## Error Responses

All endpoints may return the following error responses:

### 401 Unauthorized
```json
{
    "error": "Authentication required"
}
```

### 403 Forbidden
```json
{
    "error": "Access denied"
}
```

### 404 Not Found
```json
{
    "error": "Resource not found"
}
```

### 429 Too Many Requests
```json
{
    "error": "Rate limit exceeded",
    "retry_after": 60
}
```

### 500 Internal Server Error
```json
{
    "error": "Internal server error"
}
```

## Rate Limiting

API endpoints are rate limited to:
- 100 requests per minute for authenticated users
- 20 requests per minute for unauthenticated endpoints

Rate limit headers are included in all responses:
- `X-RateLimit-Limit`: Maximum requests allowed
- `X-RateLimit-Remaining`: Requests remaining
- `X-RateLimit-Reset`: Unix timestamp when limit resets