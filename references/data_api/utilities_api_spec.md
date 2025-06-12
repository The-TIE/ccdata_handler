# CryptoCompare "Utilities API" Specification

This document outlines the key endpoints, parameters, and example responses for the CryptoCompare "Utilities API" used in this project.

---

## Rate Limit Verification

This endpoint allows clients to check their current rate limit status. Making a call to this endpoint counts against your rate limit. It is recommended to use the X-RateLimit-* headers returned in each response to monitor your rate limits without calling this endpoint directly.

### Endpoint

`GET /admin/v2/rate/limit`

### Parameters

None

### Example Response

```json
{
    "Data": {
        "TYPE": "3000",
        "API_KEY": {
            "TYPE": "3001",
            "USED": {
                "TYPE": "3002",
                "SECOND": 1,
                "MINUTE": 1,
                "HOUR": 2,
                "DAY": 2141,
                "MONTH": 9894
            },
            "MAX": {
                "TYPE": "3003",
                "MONTH": 50000000,
                "DAY": 5000000,
                "HOUR": 300000,
                "MINUTE": 6000,
                "SECOND": 100,
                "SOFT_CAP_ALLOWANCE_MULTIPLIER": 1.1
            },
            "REMAINING": {
                "TYPE": "3004",
                "SECOND": 99,
                "MINUTE": 5999,
                "HOUR": 299998,
                "DAY": 4997859,
                "MONTH": 49990106
            }
        },
        "AUTH_KEY": {
            "TYPE": "3001",
            "USED": {
                "TYPE": "3002",
                "SECOND": 0,
                "MINUTE": 0,
                "HOUR": 0,
                "DAY": 0,
                "MONTH": 0
            },
            "MAX": {
                "TYPE": "3003",
                "MONTH": 200000,
                "DAY": 40000,
                "HOUR": 10000,
                "MINUTE": 1000,
                "SECOND": 20,
                "SOFT_CAP_ALLOWANCE_MULTIPLIER": 1.2
            },
            "REMAINING": {
                "TYPE": "3004",
                "SECOND": 20,
                "MINUTE": 1000,
                "HOUR": 10000,
                "DAY": 40000,
                "MONTH": 200000
            }
        }
    },
    "Err": {}
}
```