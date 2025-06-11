# CryptoCompare "Data API" Specification

This document outlines the key endpoints, parameters, and example responses for the CryptoCompare "Data API" used in this project.

---

## Historical OHLCV + Day

*   **Endpoint**: `/spot/v1/historical/days`
*   **Method**: `GET`
*   **Description**: Delivers daily aggregated candlestick data for specific cryptocurrency instruments across selected exchanges. It offers vital trading metrics, including open, high, low, close (OHLC) prices, and trading volumes, both in base and quote currencies. This data is key for understanding historical price movements and market behavior, allowing for detailed analysis of trading patterns and trends over time.
*   **Cache**: 300 seconds

### Parameters

*   **`market`** (string) *required*
    *   **Description**: The market / exchange under consideration (e.g. `gemini`, `kraken`, `coinbase`, etc).
*   **`instrument`** (string) *required*
    *   **Description**: A mapped and/or unmapped instrument to retrieve for a specific market (e.g., `BTC-USD`).
    *   **Constraints**: Min length: 1, Max length: 500
*   **`groups`** (array of strings)
    *   **Description**: When requesting historical entries you can filter by specific groups of interest. If left empty it will get all data that your account is allowed to access.
    *   **Allowed Values**: `ID`, `MAPPING`, `MAPPING_ADVANCED`, `OHLC`, `OHLC_TRADE`, `TRADE`, `VOLUME`
*   **`limit`** (integer)
    *   **Description**: The number of data points to return.
    *   **Constraints**: Minimum: 1, Maximum: 5000
    *   **Default**: `30`
*   **`to_ts`** (integer, Unix timestamp)
    *   **Description**: Returns historical data up to and including this Unix timestamp. When using the `to_ts` parameter to paginate through data, the earliest timestamp in the next batch will also appear as the latest timestamp in the next batch.
*   **`aggregate`** (integer)
    *   **Description**: The number of points to aggregate for each returned value.
    *   **Constraints**: Minimum: 1, Maximum: 30
    *   **Default**: `1`
*   **`fill`** (boolean)
    *   **Description**: Boolean value, if set to `false` or `0` we will not return data points for periods with no trading activity.
    *   **Default**: `true`
*   **`apply_mapping`** (boolean)
    *   **Description**: Determines if provided instrument values are converted according to internal mappings.
    *   **Default**: `true`
*   **`response_format`** (string)
    *   **Description**: This parameter allows you to choose the format of the data response from the API.
    *   **Allowed Values**: `JSON`, `CSV`

### Example Response (Concise Schema)

```json
{
    "Data": {
        "type": "array",
        "items": {
            "type": "object",
            "properties": {
                "UNIT": { "type": "string", "description": "Historical period unit (MINUTE, HOUR, DAY)." },
                "TIMESTAMP": { "type": "integer", "description": "Unix timestamp of period start." },
                "TYPE": { "type": "string", "description": "Message type." },
                "MARKET": { "type": "string", "description": "Exchange name." },
                "INSTRUMENT": { "type": "string", "description": "Unmapped instrument ID." },
                "MAPPED_INSTRUMENT": { "type": "string", "description": "Mapped instrument ID (BASE-QUOTE)." },
                "BASE": { "type": "string", "description": "Base asset symbol." },
                "QUOTE": { "type": "string", "description": "Quote asset symbol." },
                "BASE_ID": { "type": "number", "description": "Internal CCData ID for base asset." },
                "QUOTE_ID": { "type": "number", "description": "Internal CCData ID for quote asset." },
                "TRANSFORM_FUNCTION": { "type": "string", "description": "Data transformation function." },
                "OPEN": { "type": "number", "description": "Open price." },
                "HIGH": { "type": "number", "description": "High price." },
                "LOW": { "type": "number", "description": "Low price." },
                "CLOSE": { "type": "number", "description": "Close price." },
                "FIRST_TRADE_TIMESTAMP": { "type": "integer", "description": "Timestamp of first trade." },
                "LAST_TRADE_TIMESTAMP": { "type": "integer", "description": "Timestamp of last trade." },
                "FIRST_TRADE_PRICE": { "type": "number", "description": "Price of first trade." },
                "HIGH_TRADE_PRICE": { "type": "number", "description": "Highest trade price." },
                "HIGH_TRADE_TIMESTAMP": { "type": "integer", "description": "Timestamp of highest trade." },
                "LOW_TRADE_PRICE": { "type": "number", "description": "Lowest trade price." },
                "LOW_TRADE_TIMESTAMP": { "type": "integer", "description": "Timestamp of lowest trade." },
                "LAST_TRADE_PRICE": { "type": "number", "description": "Last trade price." },
                "TOTAL_TRADES": { "type": "number", "description": "Total number of trades." },
                "TOTAL_TRADES_BUY": { "type": "number", "description": "Total BUY trades." },
                "TOTAL_TRADES_SELL": { "type": "number", "description": "Total SELL trades." },
                "TOTAL_TRADES_UNKNOWN": { "type": "number", "description": "Total UNKNOWN trades." },
                "VOLUME": { "type": "number", "description": "Volume in base asset." },
                "QUOTE_VOLUME": { "type": "number", "description": "Volume in quote asset." },
                "VOLUME_BUY": { "type": "number", "description": "BUY volume in base asset." },
                "QUOTE_VOLUME_BUY": { "type": "number", "description": "BUY volume in quote asset." },
                "VOLUME_SELL": { "type": "number", "description": "SELL volume in base asset." },
                "QUOTE_VOLUME_SELL": { "type": "number", "description": "SELL volume in quote asset." },
                "VOLUME_UNKNOWN": { "type": "number", "description": "UNKNOWN volume in base asset." },
                "QUOTE_VOLUME_UNKNOWN": { "type": "number", "description": "UNKNOWN volume in quote asset." }
            }
        }
    },
    "Err": { "type": "object", "properties": {} }
}
```

---

## Historical OHLCV + Hour

*   **Endpoint**: `/spot/v1/historical/hours`
*   **Method**: `GET`
*   **Description**: Delivers hourly aggregated candlestick data for specific cryptocurrency instruments across selected exchanges. It offers vital trading metrics, including open, high, low, close (OHLC) prices, and trading volumes, both in base and quote currencies. This data is key for understanding historical price movements and market behavior, allowing for detailed analysis of trading patterns and trends over time.
*   **Cache**: 300 seconds

### Parameters

*   **`market`** (string) *required*
    *   **Description**: The market / exchange under consideration (e.g. `gemini`, `kraken`, `coinbase`, etc).
*   **`instrument`** (string) *required*
    *   **Description**: A mapped and/or unmapped instrument to retrieve for a specific market (e.g., `BTC-USD`).
    *   **Constraints**: Min length: 1, Max length: 500
*   **`groups`** (array of strings)
    *   **Description**: When requesting historical entries you can filter by specific groups of interest. If left empty it will get all data that your account is allowed to access.
    *   **Allowed Values**: `ID`, `MAPPING`, `MAPPING_ADVANCED`, `OHLC`, `OHLC_TRADE`, `TRADE`, `VOLUME`
*   **`limit`** (integer)
    *   **Description**: The number of data points to return.
    *   **Constraints**: Minimum: 1, Maximum: 5000
    *   **Default**: `168`
*   **`to_ts`** (integer, Unix timestamp)
    *   **Description**: Returns historical data up to and including this Unix timestamp. When using the `to_ts` parameter to paginate through data, the earliest timestamp in the next batch will also appear as the latest timestamp in the next batch.
*   **`aggregate`** (integer)
    *   **Description**: The number of points to aggregate for each returned value.
    *   **Constraints**: Minimum: 1, Maximum: 30
    *   **Default**: `1`
*   **`fill`** (boolean)
    *   **Description**: Boolean value, if set to `false` or `0` we will not return data points for periods with no trading activity.
    *   **Default**: `true`
*   **`apply_mapping`** (boolean)
    *   **Description**: Determines if provided instrument values are converted according to internal mappings.
    *   **Default**: `true`
*   **`response_format`** (string)
    *   **Description**: This parameter allows you to choose the format of the data response from the API.
    *   **Allowed Values**: `JSON`, `CSV`

### Example Response (Concise Schema)

```json
{
    "Data": {
        "type": "array",
        "items": {
            "type": "object",
            "properties": {
                "UNIT": { "type": "string", "description": "Historical period unit (MINUTE, HOUR, DAY)." },
                "TIMESTAMP": { "type": "integer", "description": "Unix timestamp of period start." },
                "TYPE": { "type": "string", "description": "Message type." },
                "MARKET": { "type": "string", "description": "Exchange name." },
                "INSTRUMENT": { "type": "string", "description": "Unmapped instrument ID." },
                "MAPPED_INSTRUMENT": { "type": "string", "description": "Mapped instrument ID (BASE-QUOTE)." },
                "BASE": { "type": "string", "description": "Base asset symbol." },
                "QUOTE": { "type": "string", "description": "Quote asset symbol." },
                "BASE_ID": { "type": "number", "description": "Internal CCData ID for base asset." },
                "QUOTE_ID": { "type": "number", "description": "Internal CCData ID for quote asset." },
                "TRANSFORM_FUNCTION": { "type": "string", "description": "Data transformation function." },
                "OPEN": { "type": "number", "description": "Open price." },
                "HIGH": { "type": "number", "description": "High price." },
                "LOW": { "type": "number", "description": "Low price." },
                "CLOSE": { "type": "number", "description": "Close price." },
                "FIRST_TRADE_TIMESTAMP": { "type": "integer", "description": "Timestamp of first trade." },
                "LAST_TRADE_TIMESTAMP": { "type": "integer", "description": "Timestamp of last trade." },
                "FIRST_TRADE_PRICE": { "type": "number", "description": "Price of first trade." },
                "HIGH_TRADE_PRICE": { "type": "number", "description": "Highest trade price." },
                "HIGH_TRADE_TIMESTAMP": { "type": "integer", "description": "Timestamp of highest trade." },
                "LOW_TRADE_PRICE": { "type": "number", "description": "Lowest trade price." },
                "LOW_TRADE_TIMESTAMP": { "type": "integer", "description": "Timestamp of lowest trade." },
                "LAST_TRADE_PRICE": { "type": "number", "description": "Last trade price." },
                "TOTAL_TRADES": { "type": "number", "description": "Total number of trades." },
                "TOTAL_TRADES_BUY": { "type": "number", "description": "Total BUY trades." },
                "TOTAL_TRADES_SELL": { "type": "number", "description": "Total SELL trades." },
                "TOTAL_TRADES_UNKNOWN": { "type": "number", "description": "Total UNKNOWN trades." },
                "VOLUME": { "type": "number", "description": "Volume in base asset." },
                "QUOTE_VOLUME": { "type": "number", "description": "Volume in quote asset." },
                "VOLUME_BUY": { "type": "number", "description": "BUY volume in base asset." },
                "QUOTE_VOLUME_BUY": { "type": "number", "description": "BUY volume in quote asset." },
                "VOLUME_SELL": { "type": "number", "description": "SELL volume in base asset." },
                "QUOTE_VOLUME_SELL": { "type": "number", "description": "SELL volume in quote asset." },
                "VOLUME_UNKNOWN": { "type": "number", "description": "UNKNOWN volume in base asset." },
                "QUOTE_VOLUME_UNKNOWN": { "type": "number", "description": "UNKNOWN volume in quote asset." }
            }
        }
    },
    "Err": { "type": "object", "properties": {} }
}
```

---

## Historical OHLCV + Minute

*   **Endpoint**: `/spot/v1/historical/minutes`
*   **Method**: `GET`
*   **Description**: Delivers minute aggregated candlestick data for specific cryptocurrency instruments across selected exchanges. It offers vital trading metrics, including open, high, low, close (OHLC) prices, and trading volumes, both in base and quote currencies. This data is key for understanding historical price movements and market behavior, allowing for detailed analysis of trading patterns and trends over time.
*   **Cache**: 300 seconds

### Parameters

*   **`market`** (string) *required*
    *   **Description**: The market / exchange under consideration (e.g. `gemini`, `kraken`, `coinbase`, etc).
*   **`instrument`** (string) *required*
    *   **Description**: A mapped and/or unmapped instrument to retrieve for a specific market (e.g., `BTC-USD`).
    *   **Constraints**: Min length: 1, Max length: 500
*   **`groups`** (array of strings)
    *   **Description**: When requesting historical entries you can filter by specific groups of interest. If left empty it will get all data that your account is allowed to access.
    *   **Allowed Values**: `ID`, `MAPPING`, `MAPPING_ADVANCED`, `OHLC`, `OHLC_TRADE`, `TRADE`, `VOLUME`
*   **`limit`** (integer)
    *   **Description**: The number of data points to return.
    *   **Constraints**: Minimum: 1, Maximum: 5000
    *   **Default**: `1440`
*   **`to_ts`** (integer, Unix timestamp)
    *   **Description**: Returns historical data up to and including this Unix timestamp. When using the `to_ts` parameter to paginate through data, the earliest timestamp in the next batch will also appear as the latest timestamp in the next batch.
*   **`aggregate`** (integer)
    *   **Description**: The number of points to aggregate for each returned value.
    *   **Constraints**: Minimum: 1, Maximum: 30
    *   **Default**: `1`
*   **`fill`** (boolean)
    *   **Description**: Boolean value, if set to `false` or `0` we will not return data points for periods with no trading activity.
    *   **Default**: `true`
*   **`apply_mapping`** (boolean)
    *   **Description**: Determines if provided instrument values are converted according to internal mappings.
    *   **Default**: `true`
*   **`response_format`** (string)
    *   **Description**: This parameter allows you to choose the format of the data response from the API.
    *   **Allowed Values**: `JSON`, `CSV`

### Example Response (Concise Schema)

```json
{
    "Data": {
        "type": "array",
        "items": {
            "type": "object",
            "properties": {
                "UNIT": { "type": "string", "description": "Historical period unit (MINUTE, HOUR, DAY)." },
                "TIMESTAMP": { "type": "integer", "description": "Unix timestamp of period start." },
                "TYPE": { "type": "string", "description": "Message type." },
                "MARKET": { "type": "string", "description": "Exchange name." },
                "INSTRUMENT": { "type": "string", "description": "Unmapped instrument ID." },
                "MAPPED_INSTRUMENT": { "type": "string", "description": "Mapped instrument ID (BASE-QUOTE)." },
                "BASE": { "type": "string", "description": "Base asset symbol." },
                "QUOTE": { "type": "string", "description": "Quote asset symbol." },
                "BASE_ID": { "type": "number", "description": "Internal CCData ID for base asset." },
                "QUOTE_ID": { "type": "number", "description": "Internal CCData ID for quote asset." },
                "TRANSFORM_FUNCTION": { "type": "string", "description": "Data transformation function." },
                "OPEN": { "type": "number", "description": "Open price." },
                "HIGH": { "type": "number", "description": "High price." },
                "LOW": { "type": "number", "description": "Low price." },
                "CLOSE": { "type": "number", "description": "Close price." },
                "FIRST_TRADE_TIMESTAMP": { "type": "integer", "description": "Timestamp of first trade." },
                "LAST_TRADE_TIMESTAMP": { "type": "integer", "description": "Timestamp of last trade." },
                "FIRST_TRADE_PRICE": { "type": "number", "description": "Price of first trade." },
                "HIGH_TRADE_PRICE": { "type": "number", "description": "Highest trade price." },
                "HIGH_TRADE_TIMESTAMP": { "type": "integer", "description": "Timestamp of highest trade." },
                "LOW_TRADE_PRICE": { "type": "number", "description": "Lowest trade price." },
                "LOW_TRADE_TIMESTAMP": { "type": "integer", "description": "Timestamp of lowest trade." },
                "LAST_TRADE_PRICE": { "type": "number", "description": "Last trade price." },
                "TOTAL_TRADES": { "type": "number", "description": "Total number of trades." },
                "TOTAL_TRADES_BUY": { "type": "number", "description": "Total BUY trades." },
                "TOTAL_TRADES_SELL": { "type": "number", "description": "Total SELL trades." },
                "TOTAL_TRADES_UNKNOWN": { "type": "number", "description": "Total UNKNOWN trades." },
                "VOLUME": { "type": "number", "description": "Volume in base asset." },
                "QUOTE_VOLUME": { "type": "number", "description": "Volume in quote asset." },
                "VOLUME_BUY": { "type": "number", "description": "BUY volume in base asset." },
                "QUOTE_VOLUME_BUY": { "type": "number", "description": "BUY volume in quote asset." },
                "VOLUME_SELL": { "type": "number", "description": "SELL volume in base asset." },
                "QUOTE_VOLUME_SELL": { "type": "number", "description": "SELL volume in quote asset." },
                "VOLUME_UNKNOWN": { "type": "number", "description": "UNKNOWN volume in base asset." },
                "QUOTE_VOLUME_UNKNOWN": { "type": "number", "description": "UNKNOWN volume in quote asset." }
            }
        }
    },
    "Err": { "type": "object", "properties": {} }
}
```

---

## Top List General

*   **Endpoint**: `/asset/v1/top/list`
*   **Method**: `GET`
*   **Description**: The Toplist endpoint provides ranked overviews of digital assets and industries based on critical financial metrics like market capitalization, trading volume, and price changes. It streamlines market analysis by presenting leading assets and industries in the cryptocurrency space, using pagination to efficiently navigate extensive data across multiple toplists.
*   **Cache**: 30 seconds

### Parameters

*   **`page`** (integer)
    *   **Description**: The page number for the request to get {page_size} coins at the time.
    *   **Constraints**: Minimum: 1, Maximum: 1000
    *   **Default**: `1`
*   **`page_size`** (integer)
    *   **Description**: The number of items returned per page.
    *   **Constraints**: Minimum: 10, Maximum: 100
    *   **Default**: `100`
*   **`sort_by`** (string)
    *   **Description**: Sort by field.
    *   **Allowed Values**: `CREATED_ON`, `LAUNCH_DATE`, `UPDATED_ON`, `PRICE_USD`, `CIRCULATING_MKT_CAP_USD`, `TOTAL_MKT_CAP_USD`, `SPOT_MOVING_24_HOUR_QUOTE_VOLUME_TOP_TIER_DIRECT_USD`, `SPOT_MOVING_24_HOUR_QUOTE_VOLUME_DIRECT_USD`, `SPOT_MOVING_24_HOUR_QUOTE_VOLUME_TOP_TIER_USD`, `SPOT_MOVING_24_HOUR_QUOTE_VOLUME_USD`, `SPOT_MOVING_24_HOUR_CHANGE_USD`, `SPOT_MOVING_24_HOUR_CHANGE_PERCENTAGE_USD`, `SPOT_MOVING_7_DAY_QUOTE_VOLUME_TOP_TIER_DIRECT_USD`, `SPOT_MOVING_7_DAY_QUOTE_VOLUME_DIRECT_USD`, `SPOT_MOVING_7_DAY_QUOTE_VOLUME_TOP_TIER_USD`, `SPOT_MOVING_7_DAY_QUOTE_VOLUME_USD`, `SPOT_MOVING_7_DAY_CHANGE_USD`, `SPOT_MOVING_7_DAY_CHANGE_PERCENTAGE_USD`, `SPOT_MOVING_30_DAY_QUOTE_VOLUME_TOP_TIER_DIRECT_USD`, `SPOT_MOVING_30_DAY_QUOTE_VOLUME_DIRECT_USD`, `SPOT_MOVING_30_DAY_QUOTE_VOLUME_TOP_TIER_USD`, `SPOT_MOVING_30_DAY_QUOTE_VOLUME_USD`, `SPOT_MOVING_30_DAY_CHANGE_USD`, `SPOT_MOVING_30_DAY_CHANGE_PERCENTAGE_USD`, `TOTAL_ENDPOINTS_WITH_ISSUES`
    *   **Default**: `CIRCULATING_MKT_CAP_USD`
*   **`sort_direction`** (string)
    *   **Description**: Sort direction.
    *   **Allowed Values**: `DESC`, `ASC`
    *   **Default**: `DESC`
*   **`groups`** (array of strings)
    *   **Description**: When requesting asset data you can filter by specific groups of interest.
    *   **Default**: `ID`, `BASIC`, `SUPPLY`, `PRICE`, `MKT_CAP`, `VOLUME`, `CHANGE`, `TOPLIST_RANK`
    *   **Allowed Values**: `ID`, `BASIC`, `SUPPORTED_PLATFORMS`, `CUSTODIANS`, `CONTROLLED_ADDRESSES`, `SECURITY_METRICS`, `SUPPLY`, `SUPPLY_ADDRESSES`, `ASSET_TYPE_SPECIFIC_METRICS`, `SOCIAL`, `TOKEN_SALE`, `EQUITY_SALE`, `RESOURCE_LINKS`, `CLASSIFICATION`, `PRICE`, `MKT_CAP`, `VOLUME`, `CHANGE`, `TOPLIST_RANK`, `DESCRIPTION`, `DESCRIPTION_SUMMARY`, `CONTACT`, `SEO`, `INTERNAL`
*   **`toplist_quote_asset`** (string)
    *   **Description**: Specify the digital asset for the quote values by providing either the CoinDesk internal asset ID, its unique SYMBOL, or the CoinDesk recommened URI.
    *   **Constraints**: Min length: 1, Max length: 100
    *   **Default**: `USD`
    *   **Example**: `USD`
*   **`asset_type`** (string)
    *   **Description**: This parameter can be used to filter the returned assets based on their type.
    *   **Allowed Values**: `BLOCKCHAIN`, `FIAT`, `TOKEN`, `STOCK`, `INDEX`, `COMMODITY`, `ETF`, ` `
    *   **Default**: ` `
*   **`asset_industry`** (string)
    *   **Allowed Values**: `PAYMENT`, `PLATFORM`, `STABLECOIN`, `CROSS_CHAIN_INFRASTRUCTURE`, `DECENTRALIZED_INFRASTRUCTURE`, `IDENTITY`, `MEMBERSHIP`, `COLLECTIBLE`, `REPUTATION`, `GOVERNANCE`, `WRAPPED_COLLATERAL`, `DECENTRALIZED_FINANCE_PROTOCOL`, `EXCHANGE_UTILITY`, `MEME`, `YIELD_FARMING`, `LIQUID_STAKED`, `GAMING`, `ARTIFICIAL_INTELLIGENCE`, `METAVERSE`, `ORACLE`, `REAL_WORLD_ASSETS`, ` `
    *   **Default**: ` `

### Example Response (Concise Schema)

```json
{
    "Data": {
        "type": "array",
        "items": {
            "type": "object",
            "properties": {
                "ID": { "type": "string", "description": "Basic identification details of the asset, such as unique identifiers." },
                "BASIC": { "type": "object", "description": "Basic metadata about the asset, including general characteristics." },
                "SUPPORTED_PLATFORMS": { "type": "object", "description": "Details of blockchain platforms or networks where the asset is supported." },
                "CUSTODIANS": { "type": "object", "description": "Information about custodians managing or holding the asset." },
                "CONTROLLED_ADDRESSES": { "type": "object", "description": "Addresses directly controlled or monitored for the asset." },
                "SECURITY_METRICS": { "type": "object", "description": "Metrics related to the security and risk evaluation of the asset." },
                "SUPPLY": { "type": "object", "description": "Information about the circulating, total, or max supply of the asset." },
                "SUPPLY_ADDRESSES": { "type": "object", "description": "Addresses holding the asset, impacting its supply dynamics." },
                "ASSET_TYPE_SPECIFIC_METRICS": { "type": "object", "description": "Metrics unique to specific types of assets, such as tokens or coins." },
                "SOCIAL": { "type": "object", "description": "Social media and community engagement data for the asset." },
                "TOKEN_SALE": { "type": "object", "description": "Information related to the asset’s token sale or ICO." },
                "EQUITY_SALE": { "type": "object", "description": "Data on equity sales associated with the asset or organization." },
                "RESOURCE_LINKS": { "type": "object", "description": "Links to external resources, such as websites or whitepapers." },
                "CLASSIFICATION": { "type": "object", "description": "Classification details like category, sector, or use case of the asset." },
                "PRICE": { "type": "object", "description": "Real-time and historical price data of the asset." },
                "MKT_CAP": { "type": "object", "description": "Market capitalization information of the asset." },
                "VOLUME": { "type": "object", "description": "Trading volume metrics, including exchange and market data." },
                "CHANGE": { "type": "object", "description": "Price or volume changes over defined time intervals." },
                "TOPLIST_RANK": { "type": "object", "description": "Ranking of the asset on toplist leaderboards based on various criteria." },
                "DESCRIPTION": { "type": "object", "description": "Detailed description of the asset, including features and purpose." },
                "DESCRIPTION_SUMMARY": { "type": "object", "description": "Concise summary of the asset’s description for quick reference." },
                "CONTACT": { "type": "object", "description": "Contact information related to the asset or its developers." },
                "SEO": { "type": "object", "description": "Search engine optimization metadata for better discoverability." },
                "INTERNAL": { "type": "object", "description": "Internal data used for asset management and administration purposes." }
            }
        }
    },
    "Err": { "type": "object", "properties": {} }
}
```

---

## Instrument Latest Tick

*   **Endpoint**: `/spot/v1/latest/tick`
*   **Method**: `GET`
*   **Description**: This endpoint provides real-time trade and market data for selected instruments on a specified exchange. It delivers the most current price details alongside aggregated data over various time periods including hourly, daily, weekly, monthly, and annually. This comprehensive dataset not only includes the latest price but also offers detailed metrics on volume, open-high-low-close (OHLC) values, and changes over specified periods, making it a valuable resource for tracking market trends and making informed trading decisions.
*   **Cache**: 10 seconds

### Parameters

*   **`market`** (string) *required*
    *   **Description**: The exchange to obtain data from.
    *   **Constraints**: Min length: 2, Max length: 30
    *   **Example**: `coinbase`
*   **`instruments`** (array of strings) *required*
    *   **Description**: A comma separated array of mapped and/or unmapped instruments to retrieve for a specific market (you can use either the instrument XXBTZUSD or mapped instrument (base - quote) BTC-USD on kraken as an example). We return the mapped version of the values by default.
    *   **Constraints**: Min items: 1, Max items: 50
    *   **Example**: `BTC-USD`, `ETH-USD`
*   **`groups`** (array of strings)
    *   **Description**: When requesting tick data you can filter by specific groups of interest. To do so just pass the groups of interest into the URL as a comma separated list. If left empty it will get all data that your account is allowed to access.
    *   **Allowed Values**: `ID`, `MAPPING`, `MAPPING_ADVANCED`, `VALUE`, `LAST_UPDATE`, `LAST_ADJUSTED`, `LAST_PROCESSED`, `TOP_OF_BOOK`, `CURRENT_HOUR`, `CURRENT_DAY`, `CURRENT_WEEK`, `CURRENT_MONTH`, `CURRENT_YEAR`, `MOVING_24_HOUR`, `MOVING_7_DAY`, `MOVING_30_DAY`, `MOVING_90_DAY`, `MOVING_180_DAY`, `MOVING_365_DAY`, `LIFETIME`
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
            "MAPPING": { "type": "object", "description": "Contains mapping information for the instrument." },
            "MAPPED_INSTRUMENT": { "type": "string", "description": "Mapped instrument ID (BASE-QUOTE)." },
            "VALUE": { "type": "number", "description": "Represents the latest value for an index or instrument, often used to track real-time price or metric changes." },
            "LAST_UPDATE": { "type": "object", "description": "Contains information about the timestamp and value of the most recent market update." },
            "LAST_ADJUSTED": { "type": "object", "description": "The LAST_ADJUSTED group captures metrics that reflect the most recent tick's adjusted values, incorporating any delayed or updated trades within the last hour. These fields are essential for providing accurate real-time insights into market activity and liquidity." },
            "LAST_PROCESSED": { "type": "object", "description": "Contains information about the timestamp and value of the last processed market update." },
            "TOP_OF_BOOK": { "type": "object", "description": "Provides the best bid and ask prices and sizes from the order book." },
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

---