# General Info API Spec

---

## All Exchanges General Info

*   **Endpoint**: `/data/exchanges/general`
*   **Method**: `GET`
*   **Description**: Returns general info and 24h volume for all the exchanges integrated with. This endpoint requires a valid API key.
*   **Cache**: 120 seconds

### Parameters

*   **`tsym`** (string)
    *   **Description**: The currency symbol to convert into.
    *   **Constraints**: Min length: 1, Max length: 30
    *   **Default**: `BTC`
*   **`extraParams`** (string)
    *   **Description**: The name of your application (recommended to send it).
    *   **Constraints**: Min length: 1, Max length: 2000
    *   **Default**: `NotAvailable`
*   **`sign`** (boolean)
    *   **Description**: If set to `true`, the server will sign the requests (by default they don't sign them). This is useful for usage in smart contracts.

### Example Response

```json
{
    "Response": "Success",
    "Message": "",
    "HasWarning": false,
    "Type": 100,
    "RateLimit": {},
    "Data": {
        "EXCHANGE_ID": {
            "Id": "string",
            "Name": "string",
            "Url": "string",
            "LogoUrl": "string",
            "ItemType": ["string"],
            "CentralizationType": "string",
            "InternalName": "string",
            "GradePoints": "number",
            "Grade": "string",
            "GradePointsSplit": { /* object with grade breakdown */ },
            "AffiliateURL": "string",
            "Country": "string",
            "OrderBook": "boolean",
            "Trades": "boolean",
            "Description": "string (long text)",
            "FullAddress": "string",
            "Fees": "string (long text)",
            "DepositMethods": "string (long text)",
            "WithdrawalMethods": "string (long text)",
            "Sponsored": "boolean",
            "Recommended": "boolean",
            "Rating": { /* object with rating details */ },
            "SortOrder": "string",
            "TOTALVOLUME24H": { /* object with 24h volume by currency */ },
            "DISPLAYTOTALVOLUME24H": { /* object with formatted 24h volume */ }
        },
        // ... other exchanges
    }
}
```

---
## GET /data/v4/all/exchanges

**Description:**  
Returns all the exchanges that CryptoCompare has integrated with. You can filter by exchange and from symbol.

**Parameters:**
- `fsym` (string, max length 30): The cryptocurrency symbol of interest
- `e` (string, max length 30): The exchange to obtain data from
- `topTier` (boolean): Set to true if you just want to return just the top tier exchanges
- `extraParams` (string, min length 1, max length 2000, default: NotAvailable): The name of your application (we recommend you send it)

**Example Response:**
```json
{
    "Response": "Success",
    "Message": "",
    "HasWarning": false,
    "Type": 100,
    "RateLimit": {},
    "Data": {
        "exchanges": {
            "Binance": {
                "isActive": true,
                "isTopTier": true,
                "pairs": {
                    "BNB": {
                        "tsyms": {
                            "TRY": {
                                "histo_minute_start_ts": 1576836000,
                                "histo_minute_start": "2019-12-20",
                                "histo_minute_end_ts": 1749220256,
                                "histo_minute_end": "2025-06-06",
                                "isActive": true
                            },
                            "USDT": {
                                "histo_minute_start_ts": 1509940463,
                                "histo_minute_start": "2017-11-06",
                                "histo_minute_end_ts": 1749220258,
                                "histo_minute_end": "2025-06-06",
                                "isActive": true
                            },
                        }
                    }
                }
            }
        }
    }
}
```