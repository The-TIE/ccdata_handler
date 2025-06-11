# CryptoCompare "Indices & Ref. Rates API" Specification

This document outlines the key endpoints, parameters, and example responses for the CryptoCompare "Indices & Ref. Rates API" used in this project.

---

## Instrument Latest Tick

*   **Endpoint**: `/index/cc/v1/latest/tick`
*   **Method**: `GET`
*   **Description**: This endpoint provides the latest tick data for selected index instruments across various indices, offering real-time insights into index values and comprehensive OHLC (Open, High, Low, Close) metrics, aggregated over multiple time intervals. By capturing the most up-to-date index information, it enables precise analysis and decision-making in a fast-moving market environment.
*   **Cache**: 10 seconds

### Parameters

*   **`market`** (string) *required*
    *   **Description**: The index family to obtain data from. The default value is cadli, our 24-hour volume-weighted average with time penalty and outlier adjustment index.
    *   **Allowed Values**: `cadli`, `cchkex`, `cchkex_eoddev`, `cchkexdev`, `ccix`, `ccixbe`, `ccixber`, `ccixbervwap`, `ccixbevwap`, `ccixdev`, `ccmvda_coint`, `ccmvda_virt`, `ccxrp`, `ccxrpperp`, `cd_mc`, `cdi_b`, `cdi_mda`, `cdi_ti`, `cdisett`, `cdmcdev`, `nasdaq_single`, `rr_spot`, `rr_vwap`, `sda`, `sgx_rr`, `sgxrt`, `sgxtwap`
    *   **Constraints**: Min length: 2, Max length: 30
    *   **Example**: `cadli`
*   **`instruments`** (array of strings) *required*
    *   **Description**: A comma separated array of instruments to retrieve for a specific market.
    *   **Constraints**: Min items: 1, Max items: 50
    *   **Example**: `BTC-USD`, `ETH-USD`
*   **`groups`** (array of strings)
    *   **Description**: When requesting tick data you can filter by specific groups of interest. To do so just pass the groups of interest into the URL as a comma separated list. If left empty it will get all data that your account is allowed to access.
    *   **Allowed Values**: `ID`, `VALUE`, `LAST_UPDATE`, `LAST_ADJUSTED`, `CURRENT_HOUR`, `CURRENT_DAY`, `CURRENT_WEEK`, `CURRENT_MONTH`, `CURRENT_YEAR`, `MOVING_24_HOUR`, `MOVING_7_DAY`, `MOVING_30_DAY`, `MOVING_90_DAY`, `MOVING_180_DAY`, `MOVING_365_DAY`, `LIFETIME`
    *   **Example**: ` `
*   **`apply_mapping`** (boolean)
    *   **Description**: Determines if provided instrument values are converted according to internal mappings. When true, values are translated (e.g., coinbase 'USDT-USDC' becomes 'USDC-USDT' and we invert the values); when false, original values are used.
    *   **Default**: `true`

### Example Response (Concise Schema)

```json
{
    "Data": {
        "type": "object",
        "properties": {
            "ID": { "type": "string", "description": "Identifies the market, instrument, or data source with key metadata." },
            "VALUE": { "type": "number", "description": "Represents the latest value for an index or instrument, often used to track real-time price or metric changes." },
            "LAST_UPDATE": { "type": "object", "description": "Contains information about the timestamp and value of the most recent market update." },
            "LAST_ADJUSTED": { "type": "object", "description": "The LAST_ADJUSTED group captures metrics that reflect the most recent tick's adjusted values, incorporating any delayed or updated trades within the last hour. These fields are essential for providing accurate real-time insights into market activity and liquidity." },
            "CURRENT_HOUR": { "type": "object", "description": "Aggregated data for the current hour. Useful for intraday analysis." },
            "CURRENT_DAY": { "type": "object", "description": "Provides metrics aggregated for the current day. Useful for tracking daily performance." },
            "CURRENT_WEEK": { "type": "object", "description": "Aggregated metrics for the current week." },
            "CURRENT_MONTH": { "type": "object", "description": "Represents data aggregated for the current calendar month." },
            "CURRENT_YEAR": { "type": "object", "description": "Aggregated data for the current calendar year." },
            "MOVING_24_HOUR": { "type": "object", "description": "Rolling 24-hour metrics, updated continuously. Useful for monitoring trends outside calendar boundaries." },
            "MOVING_7_DAY": { "type": "object", "description": "Aggregated metrics for the last 7 days, updated on a rolling basis." },
            "MOVING_30_DAY": { "type": "object", "description": "Aggregated metrics for the last 30 days, providing a rolling monthly perspective." },
            "MOVING_90_DAY": { "type": "object", "description": "Metrics for the past 90 days, giving a broader rolling quarterly view." },
            "MOVING_180_DAY": { "type": "object", "description": "Aggregated metrics for the past 180 days, useful for analyzing medium-term trends." },
            "MOVING_365_DAY": { "type": "object", "description": "Rolling metrics for the past year, providing a long-term perspective." },
            "LIFETIME": { "type": "object", "description": "Represents all-time metrics since the start of data collection for the specific market or instrument." }
        }
    },
    "Err": { "type": "object", "properties": {} }
}
```

## Instrument Historical Tick

*   **Endpoint**: `/index/cc/v1/historical/tick`
*   **Method**: `GET`
*   **Description**: This endpoint retrieves historical tick data for selected index instruments, providing a comprehensive record of past index values and OHLC (Open, High, Low, Close) metrics aggregated over various time intervals. By offering access to historical data, it supports in-depth analysis of market trends, backtesting strategies, and understanding long-term index performance.
*   **Cache**: 10 seconds

### Parameters

*   **`market`** (string) *required*
    *   **Description**: The index family to obtain data from. The default value is cadli, our 24-hour volume-weighted average with time penalty and outlier adjustment index.
    *   **Allowed Values**: `cadli`, `cchkex`, `cchkex_eoddev`, `cchkexdev`, `ccix`, `ccixbe`, `ccixber`, `ccixbervwap`, `ccixbevwap`, `ccixdev`, `ccmvda_coint`, `ccmvda_virt`, `ccxrp`, `ccxrpperp`, `cd_mc`, `cdi_b`, `cdi_mda`, `cdi_ti`, `cdisett`, `cdmcdev`, `nasdaq_single`, `rr_spot`, `rr_vwap`, `sda`, `sgx_rr`, `sgxrt`, `sgxtwap`
    *   **Constraints**: Min length: 2, Max length: 30
    *   **Example**: `cadli`
*   **`instruments`** (array of strings) *required*
    *   **Description**: A comma separated array of instruments to retrieve for a specific market.
    *   **Constraints**: Min items: 1, Max items: 50
    *   **Example**: `BTC-USD`, `ETH-USD`
*   **`groups`** (array of strings)
    *   **Description**: When requesting tick data you can filter by specific groups of interest. To do so just pass the groups of interest into the URL as a comma separated list. If left empty it will get all data that your account is allowed to access.
    *   **Allowed Values**: `ID`, `VALUE`, `LAST_UPDATE`, `LAST_ADJUSTED`, `CURRENT_HOUR`, `CURRENT_DAY`, `CURRENT_WEEK`, `CURRENT_MONTH`, `CURRENT_YEAR`, `MOVING_24_HOUR`, `MOVING_7_DAY`, `MOVING_30_DAY`, `MOVING_90_DAY`, `MOVING_180_DAY`, `MOVING_365_DAY`, `LIFETIME`
    *   **Example**: ` `
*   **`apply_mapping`** (boolean)
    *   **Description**: Determines if provided instrument values are converted according to internal mappings. When true, values are translated (e.g., coinbase 'USDT-USDC' becomes 'USDC-USDT' and we invert the values); when false, original values are used.
    *   **Default**: `true`
*   **`after_timestamp`** (integer)
    *   **Description**: Returns historical data after this timestamp (inclusive).
    *   **Constraints**: Min: 0
    *   **Example**: `1678886400`
*   **`before_timestamp`** (integer)
    *   **Description**: Returns historical data before this timestamp (inclusive).
    *   **Constraints**: Min: 0
    *   **Example**: `1678886400`
*   **`limit`** (integer)
    *   **Description**: The number of data points to return.
    *   **Constraints**: Min: 1, Max: 2000
    *   **Default**: `100`
*   **`aggregate`** (integer)
    *   **Description**: The number of ticks to aggregate into one data point.
    *   **Constraints**: Min: 1, Max: 30
    *   **Default**: `1`
*   **`sort_direction`** (string)
    *   **Description**: The direction in which to sort the results.
    *   **Allowed Values**: `asc`, `desc`
    *   **Default**: `desc`
*   **`start_date`** (string)
    *   **Description**: The start date for the historical data (YYYY-MM-DD).
    *   **Example**: `2023-01-01`
*   **`end_date`** (string)
    *   **Description**: The end date for the historical data (YYYY-MM-DD).
    *   **Example**: `2023-03-15`

### Example Response (Concise Schema)

```json
{
    "Data": {
        "ID": {
            "MARKET": "cadli",
            "INSTRUMENT": "BTC-USD",
            "LAST_UPDATE_TS": 1678886400,
            "LAST_UPDATE_VALUE": 25000.00,
            "CURRENT_HOUR_OPEN": 24900.00,
            "CURRENT_HOUR_HIGH": 25100.00,
            "CURRENT_HOUR_LOW": 24850.00,
            "CURRENT_HOUR_CLOSE": 25050.00,
            "CURRENT_DAY_OPEN": 24000.00,
            "CURRENT_DAY_HIGH": 25500.00,
            "CURRENT_DAY_LOW": 23800.00,
            "CURRENT_DAY_CLOSE": 25050.00,
            "MOVING_24_HOUR_OPEN": 24500.00,
            "MOVING_24_HOUR_HIGH": 25300.00,
            "MOVING_24_HOUR_LOW": 24200.00,
            "MOVING_24_HOUR_CLOSE": 25050.00
        }
    },
    "Err": {}
}
```

## Instrument Historical OHLCV+

*   **Endpoints**:
    *   `/index/cc/v1/historical/daily`
    *   `/index/cc/v1/historical/hourly`
    *   `/index/cc/v1/historical/minutes`
*   **Method**: `GET`
*   **Description**: These endpoints provide historical candlestick data for various indices, captured at daily, hourly, or minute intervals. The data encompasses crucial metrics such as OPEN, HIGH, LOW, CLOSE, VOLUME and additional trading-derived values (OHLCV+), offering a comprehensive view of an index's historical performance. This information is essential for conducting in-depth market analyses and making informed decisions based on past trends.
*   **Cache**: 300 seconds

### Parameters

*   **`market`** (string) *required*
    *   **Description**: The index family to obtain data from. The default value is cadli, our 24-hour volume-weighted average with time penalty and outlier adjustment index.
    *   **Allowed Values**: `cadli`, `cchkex`, `cchkex_eoddev`, `cchkexdev`, `ccix`, `ccixbe`, `ccixber`, `ccixbervwap`, `ccixbevwap`, `ccixdev`, `ccmvda_coint`, `ccmvda_virt`, `ccxrp`, `ccxrpperp`, `cd_mc`, `cdi_b`, `cdi_mda`, `cdi_ti`, `cdisett`, `cdmcdev`, `nasdaq_single`, `rr_spot`, `rr_vwap`, `sda`, `sgx_rr`, `sgxrt`, `sgxtwap`
    *   **Constraints**: Min length: 2, Max length: 30
    *   **Example**: `cadli`
*   **`instrument`** (string) *required*
    *   **Description**: An instrument to retrieve from a specific market. For example, BTC-USD on cadli.
    *   **Constraints**: Min length: 1, Max length: 500
    *   **Example**: `BTC-USD`
*   **`groups`** (array of strings)
    *   **Description**: When requesting historical entries you can filter by specific groups of interest. To do so just pass the groups of interest into the URL as a comma separated list. If left empty it will get all data that your account is allowed to access.
    *   **Allowed Values**: `ID`, `OHLC`, `OHLC_MESSAGE`, `MESSAGE`, `VOLUME`
    *   **Example**: ` `
*   **`limit`** (integer)
    *   **Description**: The number of data points to return. Max limit is 5000 for daily data, and 2000 for hourly and minute data.
    *   **Constraints**: Min: 1
    *   **Default**: `30`
    *   **Example**: `30`
*   **`to_ts`** (integer)
    *   **Description**: Returns historical data up to and including this Unix timestamp. When using the to_ts parameter to paginate through data, the earliest timestamp in the current batch will also appear as the latest timestamp in the next batch. To avoid duplicates, you should either deduplicate the overlapping timestamp or adjust the to_ts value to skip the duplicate. Adjustments should be made as follows: subtract 60 seconds for minute data, 3600 seconds for hourly data, or 86400 seconds for daily data. To retrieve all available historical data, use limit=2000 and continue requesting in batches. &limit=2000&to_ts=[adjusted earliest Unix timestamp received]. The to_ts parameter must be in seconds since the epoch.
    **`aggregate`** (integer)
    *   **Description**: The number of points to aggregate for each returned value. E.g. passing 5 on a minute histo data endpoint will return data at 5 minute intervals. You are still limited to a maximum of 2000 minute points so the maximum you can get is 400 5 minutes interval entries. The timestamp (to_ts) you provide determines the last full aggregation bucket. If to_ts falls within an interval, the returned data will include the entire interval that to_ts belongs to.
    *   **Constraints**: Min: 1 Max: 30
    *   **Default**: 1
    *   **Example**: 1
*   **`fill`** (boolean)
    *   **Description**: Boolean value, if set to false or 0 we will not return data points for periods with no trading activity.
    *   **Default**: `true`
    *   **Example**: `true`
*   **`apply_mapping`** (boolean)
    *   **Description**: Determines if provided instrument values are converted according to internal mappings. When true, values are translated (e.g., coinbase 'USDT-USDC' becomes 'USDC-USDT' and we invert the values); when false, original values are used.
    *   **Default**: `true`
    *   **Example**: `true`
*   **`response_format`** (string)
    *   **Description**: This parameter allows you to choose the format of the data response from the API. Select "JSON" for a structured JSON object, suitable for programmatic access and manipulation. Select "CSV" for a text file that includes a header row and multiple data rows, with comma-separated values and new line delimiters, ideal for spreadsheet applications or bulk data processing.
    *   **Allowed Values**: `JSON`, `CSV`
    *   **Default**: `JSON`
    *   **Example**: `JSON`

### Example Response (Concise Schema)

```json
{
    "Data": [
        {
            "UNIT": "DAY",
            "TIMESTAMP": 1749168000,
            "TYPE": "267",
            "MARKET": "cadli",
            "INSTRUMENT": "BTC-USD",
            "OPEN": 101626.224558759,
            "HIGH": 105407.407291189,
            "LOW": 101235.692388345,
            "CLOSE": 104394.303202528,
            "FIRST_MESSAGE_TIMESTAMP": 1749168000,
            "LAST_MESSAGE_TIMESTAMP": 1749238176,
            "FIRST_MESSAGE_VALUE": 101626.224865382,
            "HIGH_MESSAGE_VALUE": 105407.407291189,
            "HIGH_MESSAGE_TIMESTAMP": 1749223006,
            "LOW_MESSAGE_VALUE": 101235.692388345,
            "LOW_MESSAGE_TIMESTAMP": 1749169364,
            "LAST_MESSAGE_VALUE": 104394.303202528,
            "TOTAL_INDEX_UPDATES": 226581,
            "VOLUME": 173585.090508789,
            "QUOTE_VOLUME": 17999414973.1633,
            "VOLUME_TOP_TIER": 97720.4873760853,
            "QUOTE_VOLUME_TOP_TIER": 10136398898.0737,
            "VOLUME_DIRECT": 24353.12347664,
            "QUOTE_VOLUME_DIRECT": 2525680969.62539,
            "VOLUME_TOP_TIER_DIRECT": 20990.8431262,
            "QUOTE_VOLUME_TOP_TIER_DIRECT": 2177261048.31427
        }
    ],
    "Err": {}
}
```

---