# CryptoCompare "Min API" Specification

This document outlines the key endpoints, parameters, and example responses for the CryptoCompare "Min API" used in this project.

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

## Daily Pair OHLCV

*   **Endpoint**: `/data/v2/histoday`
*   **Method**: `GET`
*   **Description**: Get open, high, low, close, volumeFrom and volumeTo from the daily historical data. The values are based on 00:00 GMT time. If `e=CCCAGG` and `tryConversion=true`, it attempts conversion through BTC or ETH to determine the best possible path.
*   **Cache**: 610 seconds

### Parameters

*   **`fsym`** (string) *required*
    *   **Description**: The cryptocurrency symbol of interest.
    *   **Constraints**: Min length: 1, Max length: 30
*   **`tsym`** (string) *required*
    *   **Description**: The currency symbol to convert into.
    *   **Constraints**: Min length: 1, Max length: 30
*   **`tryConversion`** (boolean)
    *   **Description**: If set to `false`, it will try to get only direct trading values. This parameter is only valid for `e=CCCAGG` value.
    *   **Default**: `true`
*   **`e`** (string)
    *   **Description**: The exchange to obtain data from.
    *   **Constraints**: Min length: 2, Max length: 30
    *   **Default**: `CCCAGG`
*   **`aggregate`** (int)
    *   **Description**: Time period to aggregate the data over (for daily it's days, for hourly it's hours and for minute histo it's minutes).
    *   **Default**: `1`
*   **`limit`** (int)
    *   **Description**: The number of data points to return. If `limit * aggregate > 2000` we reduce the limit param on our side. So a limit of 1000 and an aggerate of 4 would only return 2000 (max points) / 4 (aggregation size) = 500 total points + current one so 501.
    *   **Default**: `30`
*   **`allData`** (boolean)
    *   **Description**: Returns all data (only available on histo day).
*   **`toTs`** (timestamp)
    *   **Description**: Returns historical data before that timestamp. If you want to get all the available historical data, you can use `limit=2000` and keep going back in time using the `toTs` param.
*   **`explainPath`** (boolean)
    *   **Description**: If set to `true`, each point calculated will return the available options it used to make the calculation path decision.
*   **`extraParams`** (string)
    *   **Description**: The name of your application (recommended to send it).
*   **`sign`** (boolean)
    *   **Description**: If set to `true`, the server will sign the requests.

### Example Response

```json
{
    "Response": "Success",
    "Message": "",
    "HasWarning": false,
    "Type": 100,
    "RateLimit": {},
    "Data": {
        "Aggregated": "boolean",
        "TimeFrom": "timestamp",
        "TimeTo": "timestamp",
        "Data": [
            {
                "time": "timestamp",
                "high": "number",
                "low": "number",
                "open": "number",
                "volumefrom": "number",
                "volumeto": "number",
                "close": "number",
                "conversionType": "string",
                "conversionSymbol": "string"
            }
            // ... more historical data points
        ]
    }
}
```

---

## Hourly Pair OHLCV

*   **Endpoint**: `/data/v2/histohour`
*   **Method**: `GET`
*   **Description**: Get open, high, low, close, volumeFrom and volumeTo from the hourly historical data. If `e=CCCAGG` and `tryConversion=true`, it attempts conversion through BTC or ETH to determine the best possible path.
*   **Cache**: 610 seconds

### Parameters

*   **`fsym`** (string) *required*
    *   **Description**: The cryptocurrency symbol of interest.
    *   **Constraints**: Min length: 1, Max length: 30
*   **`tsym`** (string) *required*
    *   **Description**: The currency symbol to convert into.
    *   **Constraints**: Min length: 1, Max length: 30
*   **`tryConversion`** (boolean)
    *   **Description**: If set to `false`, it will try to get only direct trading values. This parameter is only valid for `e=CCCAGG` value.
    *   **Default**: `true`
*   **`e`** (string)
    *   **Description**: The exchange to obtain data from.
    *   **Constraints**: Min length: 2, Max length: 30
    *   **Default**: `CCCAGG`
*   **`aggregate`** (int)
    *   **Description**: Time period to aggregate the data over (for daily it's days, for hourly it's hours and for minute histo it's minutes).
    *   **Default**: `1`
*   **`limit`** (int)
    *   **Description**: The number of data points to return. If `limit * aggregate > 2000` we reduce the limit param on our side. So a limit of 1000 and an aggerate of 4 would only return 2000 (max points) / 4 (aggregation size) = 500 total points + current one so 501.
    *   **Default**: `168`
*   **`toTs`** (timestamp)
    *   **Description**: Returns historical data before that timestamp. If you want to get all the available historical data, you can use `limit=2000` and keep going back in time using the `toTs` param.
*   **`explainPath`** (boolean)
    *   **Description**: If set to `true`, each point calculated will return the available options it used to make the calculation path decision.
*   **`extraParams`** (string)
    *   **Description**: The name of your application (recommended to send it).
*   **`sign`** (boolean)
    *   **Description**: If set to `true`, the server will sign the requests.

### Example Response

```json
{
    "Response": "Success",
    "Message": "",
    "HasWarning": false,
    "Type": 100,
    "RateLimit": {},
    "Data": {
        "Aggregated": "boolean",
        "TimeFrom": "timestamp",
        "TimeTo": "timestamp",
        "Data": [
            {
                "time": "timestamp",
                "high": "number",
                "low": "number",
                "open": "number",
                "volumefrom": "number",
                "volumeto": "number",
                "close": "number",
                "conversionType": "string",
                "conversionSymbol": "string"
            }
            // ... more historical data points
        ]
    }
}
```

---

## Minute Pair OHLCV

*   **Endpoint**: `/data/v2/histominute`
*   **Method**: `GET`
*   **Description**: Get open, high, low, close, volumeFrom and volumeTo from the each minute historical data. This data is only stored for 7 days. If `e=CCCAGG` and `tryConversion=true`, it attempts conversion through BTC or ETH to determine the best possible path.
*   **Cache**: 40 seconds

### Parameters

*   **`fsym`** (string) *required*
    *   **Description**: The cryptocurrency symbol of interest.
    *   **Constraints**: Min length: 1, Max length: 30
*   **`tsym`** (string) *required*
    *   **Description**: The currency symbol to convert into.
    *   **Constraints**: Min length: 1, Max length: 30
*   **`tryConversion`** (boolean)
    *   **Description**: If set to `false`, it will try to get only direct trading values. This parameter is only valid for `e=CCCAGG` value.
    *   **Default**: `true`
*   **`e`** (string)
    *   **Description**: The exchange to obtain data from.
    *   **Constraints**: Min length: 2, Max length: 30
    *   **Default**: `CCCAGG`
*   **`aggregate`** (int)
    *   **Description**: Time period to aggregate the data over (for daily it's days, for hourly it's hours and for minute histo it's minutes).
    *   **Default**: `1`
*   **`limit`** (int)
    *   **Description**: The number of data points to return. If `limit * aggregate > 2000` we reduce the limit param on our side. So a limit of 1000 and an aggerate of 4 would only return 2000 (max points) / 4 (aggregation size) = 500 total points + current one so 501.
    *   **Default**: `1440`
*   **`toTs`** (timestamp)
    *   **Description**: Returns historical data before that timestamp. If you want to get all the available historical data, you can use `limit=2000` and keep going back in time using the `toTs` param.
*   **`explainPath`** (boolean)
    *   **Description**: If set to `true`, each point calculated will return the available options it used to make the calculation path decision.
*   **`extraParams`** (string)
    *   **Description**: The name of your application (recommended to send it).
*   **`sign`** (boolean)
    *   **Description**: If set to `true`, the server will sign the requests.

### Example Response

```json
{
    "Response": "Success",
    "Message": "",
    "HasWarning": false,
    "Type": 100,
    "RateLimit": {},
    "Data": {
        "Aggregated": "boolean",
        "TimeFrom": "timestamp",
        "TimeTo": "timestamp",
        "Data": [
            {
                "time": "timestamp",
                "high": "number",
                "low": "number",
                "open": "number",
                "volumefrom": "number",
                "volumeto": "number",
                "close": "number",
                "conversionType": "string",
                "conversionSymbol": "string"
            }
            // ... more historical data points
        ]
    }
}
```

---