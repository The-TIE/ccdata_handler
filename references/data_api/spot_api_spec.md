# CryptoCompare "Spot API" Specification

This document outlines the key endpoints, parameters, and example responses for the CryptoCompare "Spot API" used in this project.

---

## `/spot/v1/latest/tick`

**Description:**  
This endpoint provides real-time trade and market data for selected instruments on a specified exchange. It delivers the most current price details alongside aggregated data over various time periods including hourly, daily, weekly, monthly, and annually. This comprehensive dataset not only includes the latest price but also offers detailed metrics on volume, open-high-low-close (OHLC) values, and changes over specified periods, making it a valuable resource for tracking market trends and making informed trading decisions.

**Parameters:**

- `market` (query, string, required): The exchange to obtain data from.  
  Example: `coinbase`

- `instruments` (query, array of strings, required): A comma separated array of mapped and/or unmapped instruments to retrieve for a specific market (e.g., `BTC-USD`, `ETH-USD`).  
  Example: `["BTC-USD", "ETH-USD"]`

- `groups` (query, array of strings, optional): Filter by specific groups of interest.  
  Enum: ID, MAPPING, MAPPING_ADVANCED, VALUE, LAST_UPDATE, LAST_ADJUSTED, LAST_PROCESSED, TOP_OF_BOOK, CURRENT_HOUR, CURRENT_DAY, CURRENT_WEEK, CURRENT_MONTH, CURRENT_YEAR, MOVING_24_HOUR, MOVING_7_DAY, MOVING_30_DAY, MOVING_90_DAY, MOVING_180_DAY, MOVING_365_DAY, LIFETIME  
  Example: `[]`

- `apply_mapping` (query, boolean, optional): Determines if provided instrument values are converted according to internal mappings.  
  Default: true  
  Example: `true`

**Example Response:**  
_To be provided and recorded in full._

**Example Response:**

```json
{
    "Data": {
        "BTC-USD": {
            "TYPE": "953",
            "MARKET": "coinbase",
            "INSTRUMENT": "BTC-USD",
            "MAPPED_INSTRUMENT": "BTC-USD",
            "BASE": "BTC",
            "QUOTE": "USD",
            "BASE_ID": 1,
            "QUOTE_ID": 5,
            "TRANSFORM_FUNCTION": "",
            "CCSEQ": 833685870,
            "PRICE": 104642.14,
            "PRICE_FLAG": "DOWN",
            "PRICE_LAST_UPDATE_TS": 1749138432,
            "PRICE_LAST_UPDATE_TS_NS": 662000000,
            "LAST_TRADE_QUANTITY": 0.00076496,
            "LAST_TRADE_QUOTE_QUANTITY": 80.0470514144,
            "LAST_TRADE_ID": "833766300",
            "LAST_TRADE_CCSEQ": 833749924,
            "LAST_TRADE_SIDE": "SELL",
            "LAST_PROCESSED_TRADE_TS": 1749138432,
            "LAST_PROCESSED_TRADE_TS_NS": 662000000,
            "LAST_PROCESSED_TRADE_PRICE": 104642.14,
            "LAST_PROCESSED_TRADE_QUANTITY": 0.00076496,
            "LAST_PROCESSED_TRADE_QUOTE_QUANTITY": 80.0470514144,
            "LAST_PROCESSED_TRADE_SIDE": "SELL",
            "LAST_PROCESSED_TRADE_CCSEQ": 833749924,
            "BEST_BID": 104642.14,
            "BEST_BID_QUANTITY": 0.00541177,
            "BEST_BID_QUOTE_QUANTITY": 566.2991939878,
            "BEST_BID_LAST_UPDATE_TS": 1749138432,
            "BEST_BID_LAST_UPDATE_TS_NS": 485798000,
            "BEST_BID_POSITION_IN_BOOK_UPDATE_TS": 1749138432,
            "BEST_BID_POSITION_IN_BOOK_UPDATE_TS_NS": 485798000,
            "BEST_ASK": 104642.15,
            "BEST_ASK_QUANTITY": 0.14951519,
            "BEST_ASK_QUOTE_QUANTITY": 15645.5909392585,
            "BEST_ASK_LAST_UPDATE_TS": 1749138432,
            "BEST_ASK_LAST_UPDATE_TS_NS": 306927000,
            "BEST_ASK_POSITION_IN_BOOK_UPDATE_TS": 1749138432,
            "BEST_ASK_POSITION_IN_BOOK_UPDATE_TS_NS": 306927000,
            "CURRENT_HOUR_VOLUME": 235.29233747,
            "CURRENT_HOUR_VOLUME_BUY": 142.07503648,
            "CURRENT_HOUR_VOLUME_SELL": 93.21730099,
            "CURRENT_HOUR_VOLUME_UNKNOWN": 0,
            "CURRENT_HOUR_QUOTE_VOLUME": 24625926.0439238,
            "CURRENT_HOUR_QUOTE_VOLUME_BUY": 14868836.1305543,
            "CURRENT_HOUR_QUOTE_VOLUME_SELL": 9757089.91336942,
            "CURRENT_HOUR_QUOTE_VOLUME_UNKNOWN": 0,
            "CURRENT_HOUR_OPEN": 104695.9,
            "CURRENT_HOUR_HIGH": 104919.19,
            "CURRENT_HOUR_LOW": 104368.08,
            "CURRENT_HOUR_TOTAL_TRADES": 17455,
            "CURRENT_HOUR_TOTAL_TRADES_BUY": 10580,
            "CURRENT_HOUR_TOTAL_TRADES_SELL": 6875,
            "CURRENT_HOUR_TOTAL_TRADES_UNKNOWN": 0,
            "CURRENT_HOUR_CHANGE": -53.76,
            "CURRENT_HOUR_CHANGE_PERCENTAGE": -0.0513487156612628,
            "CURRENT_DAY_VOLUME": 3463.34374181,
            "CURRENT_DAY_VOLUME_BUY": 1632.40558558,
            "CURRENT_DAY_VOLUME_SELL": 1830.93815623,
            "CURRENT_DAY_VOLUME_UNKNOWN": 0,
            "CURRENT_DAY_QUOTE_VOLUME": 363373324.690689,
            "CURRENT_DAY_QUOTE_VOLUME_BUY": 171172252.543616,
            "CURRENT_DAY_QUOTE_VOLUME_SELL": 192201072.147122,
            "CURRENT_DAY_QUOTE_VOLUME_UNKNOWN": 0,
            "CURRENT_DAY_OPEN": 104753.38,
            "CURRENT_DAY_HIGH": 105999.68,
            "CURRENT_DAY_LOW": 103910.44,
            "CURRENT_DAY_TOTAL_TRADES": 238728,
            "CURRENT_DAY_TOTAL_TRADES_BUY": 133912,
            "CURRENT_DAY_TOTAL_TRADES_SELL": 104816,
            "CURRENT_DAY_TOTAL_TRADES_UNKNOWN": 0,
            "CURRENT_DAY_CHANGE": -111.24,
            "CURRENT_DAY_CHANGE_PERCENTAGE": -0.10619227751887299,
            "CURRENT_WEEK_VOLUME": 20273.74763169,
            "CURRENT_WEEK_VOLUME_BUY": 9490.28354491,
            "CURRENT_WEEK_VOLUME_SELL": 10783.46408678,
            "CURRENT_WEEK_VOLUME_UNKNOWN": 0,
            "CURRENT_WEEK_QUOTE_VOLUME": 2133902837.95665,
            "CURRENT_WEEK_QUOTE_VOLUME_BUY": 999100622.396825,
            "CURRENT_WEEK_QUOTE_VOLUME_SELL": 1134802215.55983,
            "CURRENT_WEEK_QUOTE_VOLUME_UNKNOWN": 0,
            "CURRENT_WEEK_OPEN": 105697.94,
            "CURRENT_WEEK_HIGH": 106901.68,
            "CURRENT_WEEK_LOW": 103685.23,
            "CURRENT_WEEK_TOTAL_TRADES": 1359427,
            "CURRENT_WEEK_TOTAL_TRADES_BUY": 770589,
            "CURRENT_WEEK_TOTAL_TRADES_SELL": 588838,
            "CURRENT_WEEK_TOTAL_TRADES_UNKNOWN": 0,
            "CURRENT_WEEK_CHANGE": -1055.8,
            "CURRENT_WEEK_CHANGE_PERCENTAGE": -0.998884178821271,
            "CURRENT_MONTH_VOLUME": 22643.67654733,
            "CURRENT_MONTH_VOLUME_BUY": 10644.77451482,
            "CURRENT_MONTH_VOLUME_SELL": 11998.90203251,
            "CURRENT_MONTH_VOLUME_UNKNOWN": 0,
            "CURRENT_MONTH_QUOTE_VOLUME": 2382515174.41002,
            "CURRENT_MONTH_QUOTE_VOLUME_BUY": 1120252602.00978,
            "CURRENT_MONTH_QUOTE_VOLUME_SELL": 1262262572.40027,
            "CURRENT_MONTH_QUOTE_VOLUME_UNKNOWN": 0,
            "CURRENT_MONTH_OPEN": 104645.87,
            "CURRENT_MONTH_HIGH": 106901.68,
            "CURRENT_MONTH_LOW": 103685.23,
            "CURRENT_MONTH_TOTAL_TRADES": 1634674,
            "CURRENT_MONTH_TOTAL_TRADES_BUY": 947703,
            "CURRENT_MONTH_TOTAL_TRADES_SELL": 686971,
            "CURRENT_MONTH_TOTAL_TRADES_UNKNOWN": 0,
            "CURRENT_MONTH_CHANGE": -3.73,
            "CURRENT_MONTH_CHANGE_PERCENTAGE": -0.0035644024938585703,
            "CURRENT_YEAR_VOLUME": 1539313.16916505,
            "CURRENT_YEAR_VOLUME_BUY": 765965.87999564,
            "CURRENT_YEAR_VOLUME_SELL": 773347.28916941,
            "CURRENT_YEAR_VOLUME_UNKNOWN": 0,
            "CURRENT_YEAR_QUOTE_VOLUME": 144131442302.424,
            "CURRENT_YEAR_QUOTE_VOLUME_BUY": 71569264570.3741,
            "CURRENT_YEAR_QUOTE_VOLUME_SELL": 72562177732.1414,
            "CURRENT_YEAR_QUOTE_VOLUME_UNKNOWN": 0,
            "CURRENT_YEAR_OPEN": 93354.22,
            "CURRENT_YEAR_HIGH": 112000,
            "CURRENT_YEAR_LOW": 74420.69,
            "CURRENT_YEAR_TOTAL_TRADES": 82265160,
            "CURRENT_YEAR_TOTAL_TRADES_BUY": 46516823,
            "CURRENT_YEAR_TOTAL_TRADES_SELL": 35748337,
            "CURRENT_YEAR_TOTAL_TRADES_UNKNOWN": 0,
            "CURRENT_YEAR_CHANGE": 11287.92,
            "CURRENT_YEAR_CHANGE_PERCENTAGE": 12.0914940963569,
            "MOVING_24_HOUR_VOLUME": 5031.85768914,
            "MOVING_24_HOUR_VOLUME_BUY": 2223.24615068,
            "MOVING_24_HOUR_VOLUME_SELL": 2808.61153846,
            "MOVING_24_HOUR_VOLUME_UNKNOWN": 0,
            "MOVING_24_HOUR_QUOTE_VOLUME": 528053472.107163,
            "MOVING_24_HOUR_QUOTE_VOLUME_BUY": 233227463.452843,
            "MOVING_24_HOUR_QUOTE_VOLUME_SELL": 294826008.654317,
            "MOVING_24_HOUR_QUOTE_VOLUME_UNKNOWN": 0,
            "MOVING_24_HOUR_OPEN": 105353.24,
            "MOVING_24_HOUR_HIGH": 105999.68,
            "MOVING_24_HOUR_LOW": 103910.44,
            "MOVING_24_HOUR_TOTAL_TRADES": 357890,
            "MOVING_24_HOUR_TOTAL_TRADES_BUY": 199727,
            "MOVING_24_HOUR_TOTAL_TRADES_SELL": 158163,
            "MOVING_24_HOUR_TOTAL_TRADES_UNKNOWN": 0,
            "MOVING_24_HOUR_CHANGE": -711.1,
            "MOVING_24_HOUR_CHANGE_PERCENTAGE": -0.674967376418608,
            "MOVING_7_DAY_VOLUME": 32913.44720295,
            "MOVING_7_DAY_VOLUME_BUY": 15595.78320195,
            "MOVING_7_DAY_VOLUME_SELL": 17317.664001,
            "MOVING_7_DAY_VOLUME_UNKNOWN": 0,
            "MOVING_7_DAY_QUOTE_VOLUME": 3459064585.33066,
            "MOVING_7_DAY_QUOTE_VOLUME_BUY": 1639343027.9978,
            "MOVING_7_DAY_QUOTE_VOLUME_SELL": 1819721557.33276,
            "MOVING_7_DAY_QUOTE_VOLUME_UNKNOWN": 0,
            "MOVING_7_DAY_OPEN": 105572.58,
            "MOVING_7_DAY_HIGH": 106901.68,
            "MOVING_7_DAY_LOW": 103110.01,
            "MOVING_7_DAY_TOTAL_TRADES": 2491062,
            "MOVING_7_DAY_TOTAL_TRADES_BUY": 1475023,
            "MOVING_7_DAY_TOTAL_TRADES_SELL": 1016039,
            "MOVING_7_DAY_TOTAL_TRADES_UNKNOWN": 0,
            "MOVING_7_DAY_CHANGE": -930.44,
            "MOVING_7_DAY_CHANGE_PERCENTAGE": -0.881327329501657,
            "MOVING_30_DAY_VOLUME": 210873.65115131,
            "MOVING_30_DAY_VOLUME_BUY": 101139.54133653,
            "MOVING_30_DAY_VOLUME_SELL": 109734.10981478,
            "MOVING_30_DAY_VOLUME_UNKNOWN": 0,
            "MOVING_30_DAY_QUOTE_VOLUME": 22208189708.9487,
            "MOVING_30_DAY_QUOTE_VOLUME_BUY": 10653605315.0724,
            "MOVING_30_DAY_QUOTE_VOLUME_SELL": 11554584393.8723,
            "MOVING_30_DAY_QUOTE_VOLUME_UNKNOWN": 0,
            "MOVING_30_DAY_OPEN": 96839.17,
            "MOVING_30_DAY_HIGH": 112000,
            "MOVING_30_DAY_LOW": 95800,
            "MOVING_30_DAY_TOTAL_TRADES": 12663048,
            "MOVING_30_DAY_TOTAL_TRADES_BUY": 7313873,
            "MOVING_30_DAY_TOTAL_TRADES_SELL": 5349175,
            "MOVING_30_DAY_TOTAL_TRADES_UNKNOWN": 0,
            "MOVING_30_DAY_CHANGE": 7802.97,
            "MOVING_30_DAY_CHANGE_PERCENTAGE": 8.05765889980263,
            "MOVING_90_DAY_VOLUME": 726840.17705937,
            "MOVING_90_DAY_VOLUME_BUY": 364868.57615146,
            "MOVING_90_DAY_VOLUME_SELL": 361971.60090791,
            "MOVING_90_DAY_VOLUME_UNKNOWN": 0,
            "MOVING_90_DAY_QUOTE_VOLUME": 66174116563.8267,
            "MOVING_90_DAY_QUOTE_VOLUME_BUY": 33122868612.1524,
            "MOVING_90_DAY_QUOTE_VOLUME_SELL": 33051247951.7864,
            "MOVING_90_DAY_QUOTE_VOLUME_UNKNOWN": 0,
            "MOVING_90_DAY_OPEN": 86756.98,
            "MOVING_90_DAY_HIGH": 112000,
            "MOVING_90_DAY_LOW": 74420.69,
            "MOVING_90_DAY_TOTAL_TRADES": 39687140,
            "MOVING_90_DAY_TOTAL_TRADES_BUY": 22380405,
            "MOVING_90_DAY_TOTAL_TRADES_SELL": 17306735,
            "MOVING_90_DAY_TOTAL_TRADES_UNKNOWN": 0,
            "MOVING_90_DAY_CHANGE": 17885.16,
            "MOVING_90_DAY_CHANGE_PERCENTAGE": 20.6152404106275,
            "MOVING_180_DAY_VOLUME": 1847784.37476553,
            "MOVING_180_DAY_VOLUME_BUY": 920234.83361701,
            "MOVING_180_DAY_VOLUME_SELL": 927549.54114852,
            "MOVING_180_DAY_VOLUME_UNKNOWN": 0,
            "MOVING_180_DAY_QUOTE_VOLUME": 174606921679.245,
            "MOVING_180_DAY_QUOTE_VOLUME_BUY": 86814946529.6816,
            "MOVING_180_DAY_QUOTE_VOLUME_SELL": 87791975149.6433,
            "MOVING_180_DAY_QUOTE_VOLUME_UNKNOWN": 0,
            "MOVING_180_DAY_OPEN": 99929.32,
            "MOVING_180_DAY_HIGH": 112000,
            "MOVING_180_DAY_LOW": 74420.69,
            "MOVING_180_DAY_TOTAL_TRADES": 98925302,
            "MOVING_180_DAY_TOTAL_TRADES_BUY": 56642226,
            "MOVING_180_DAY_TOTAL_TRADES_SELL": 42283076,
            "MOVING_180_DAY_TOTAL_TRADES_UNKNOWN": 0,
            "MOVING_180_DAY_CHANGE": 4712.82,
            "MOVING_180_DAY_CHANGE_PERCENTAGE": 4.71615337720701,
            "MOVING_365_DAY_VOLUME": 3988810.30434653,
            "MOVING_365_DAY_VOLUME_BUY": 1994501.58583949,
            "MOVING_365_DAY_VOLUME_SELL": 1994308.71850704,
            "MOVING_365_DAY_VOLUME_UNKNOWN": 0,
            "MOVING_365_DAY_QUOTE_VOLUME": 325409922046.673,
            "MOVING_365_DAY_QUOTE_VOLUME_BUY": 162250151349.754,
            "MOVING_365_DAY_QUOTE_VOLUME_SELL": 163159770696.987,
            "MOVING_365_DAY_QUOTE_VOLUME_UNKNOWN": 0,
            "MOVING_365_DAY_OPEN": 71121.11,
            "MOVING_365_DAY_HIGH": 112000,
            "MOVING_365_DAY_LOW": 49050.01,
            "MOVING_365_DAY_TOTAL_TRADES": 183904413,
            "MOVING_365_DAY_TOTAL_TRADES_BUY": 106720552,
            "MOVING_365_DAY_TOTAL_TRADES_SELL": 77183861,
            "MOVING_365_DAY_TOTAL_TRADES_UNKNOWN": 0,
            "MOVING_365_DAY_CHANGE": 33521.03,
            "MOVING_365_DAY_CHANGE_PERCENTAGE": 47.132321191275004,
            "LIFETIME_FIRST_TRADE_TS": 1417412037,
            "LIFETIME_VOLUME": 52853842.5246353,
            "LIFETIME_VOLUME_BUY": 25395285.8793722,
            "LIFETIME_VOLUME_SELL": 27458555.1034574,
            "LIFETIME_VOLUME_UNKNOWN": 1.53,
            "LIFETIME_QUOTE_VOLUME": 1316893677740.81,
            "LIFETIME_QUOTE_VOLUME_BUY": 646056308089.748,
            "LIFETIME_QUOTE_VOLUME_SELL": 670837363084.513,
            "LIFETIME_QUOTE_VOLUME_UNKNOWN": 459,
            "LIFETIME_OPEN": 300,
            "LIFETIME_HIGH": 112000,
            "LIFETIME_HIGH_TS": 1747935216,
            "LIFETIME_LOW": 0.06,
            "LIFETIME_LOW_TS": 1492297346,
            "LIFETIME_TOTAL_TRADES": 833671567,
            "LIFETIME_TOTAL_TRADES_BUY": 401690885,
            "LIFETIME_TOTAL_TRADES_SELL": 431980529,
            "LIFETIME_TOTAL_TRADES_UNKNOWN": 153,
            "LIFETIME_CHANGE": 104342.14,
            "LIFETIME_CHANGE_PERCENTAGE": 34780.713333333304
        },
    },
    "Err": {}
}
```

---

## `/spot/v1/historical/days`, `/spot/v1/historical/hours`, `/spot/v1/historical/minutes`

**Description:**  
These endpoints provide historical candlestick (OHLCV) data for cryptocurrency instruments across selected exchanges, at daily, hourly, or minute intervals. Each returns open, high, low, close prices and volume metrics in both base and quote currencies for the specified time granularity. Use these endpoints to analyze historical price movements, trading patterns, and market behavior at your desired resolution.

**Endpoints:**
- `/spot/v1/historical/days` (max `limit`: 5000)
- `/spot/v1/historical/hours` (max `limit`: 2000)
- `/spot/v1/historical/minutes` (max `limit`: 2000)

**Parameters:**

- `market` (query, string, required): The exchange to obtain data from.  
  Example: `binance`

- `instrument` (query, string, required): A mapped and/or unmapped instrument to retrieve for a specific market (e.g., `BTC-USDT`).  
  Example: `BTC-USDT`

- `groups` (query, array of strings, optional): Filter by specific groups of interest.  
  Enum: ID, MAPPING, MAPPING_ADVANCED, OHLC, OHLC_TRADE, TRADE, VOLUME  
  Example: `[]`

- `limit` (query, integer, optional): The number of data points to return.  
  Default: 30  
  Max: 5000 for days, 2000 for hours/minutes  
  Example: `10`

- `to_ts` (query, integer, optional): Returns historical data up to and including this Unix timestamp.  
  Example: `1622505600`

- `aggregate` (query, integer, optional): The number of points to aggregate for each returned value.  
  Default: 1, Min: 1, Max: 30  
  Example: `1`

- `fill` (query, boolean, optional): If set to false or 0, will not return data points for periods with no trading activity.  
  Default: true  
  Example: `true`

- `apply_mapping` (query, boolean, optional): Determines if provided instrument values are converted according to internal mappings.  
  Default: true  
  Example: `true`

- `response_format` (query, string, optional): Choose the format of the data response from the API.  
  Enum: JSON, CSV  
  Default: JSON  
  Example: `JSON`

**Example Response:**

```json
{
    "Data": [
        {
            "UNIT": "DAY",
            "TIMESTAMP": 1749081600,
            "TYPE": "954",
            "MARKET": "kraken",
            "INSTRUMENT": "XXBTZUSD",
            "MAPPED_INSTRUMENT": "BTC-USD",
            "BASE": "BTC",
            "QUOTE": "USD",
            "BASE_ID": 1,
            "QUOTE_ID": 5,
            "TRANSFORM_FUNCTION": "",
            "OPEN": 104745.4,
            "HIGH": 105948.1,
            "LOW": 103816.5,
            "CLOSE": 103816.6,
            "FIRST_TRADE_TIMESTAMP": 1749081600,
            "LAST_TRADE_TIMESTAMP": 1749141594,
            "FIRST_TRADE_PRICE": 104745.4,
            "HIGH_TRADE_PRICE": 105948.1,
            "HIGH_TRADE_TIMESTAMP": 1749129192,
            "LOW_TRADE_PRICE": 103816.5,
            "LOW_TRADE_TIMESTAMP": 1749141591,
            "LAST_TRADE_PRICE": 103816.6,
            "TOTAL_TRADES": 15141,
            "TOTAL_TRADES_BUY": 8963,
            "TOTAL_TRADES_SELL": 6178,
            "TOTAL_TRADES_UNKNOWN": 0,
            "VOLUME": 570.57588134,
            "QUOTE_VOLUME": 59804933.4479934,
            "VOLUME_BUY": 254.85238326,
            "QUOTE_VOLUME_BUY": 26752024.070733,
            "VOLUME_SELL": 315.72349808,
            "QUOTE_VOLUME_SELL": 33052909.3772628,
            "VOLUME_UNKNOWN": 0,
            "QUOTE_VOLUME_UNKNOWN": 0
        }
    ],
    "Err": {}
}
```
---

## `/spot/v2/historical/trades/hour`

**Description:**  
This endpoint provides detailed, standardized, and deduplicated tick-level trade data for a specified instrument on a chosen exchange, covering a specific hour. It captures every transaction executed, offering deep insights into trading activity, including price, quantity, and timestamp details. Each trade includes an individual CCSEQ (CryptoCompare Sequence) number, trade side, and both received (by us) and reported (by the exchange) timestamps with nanosecond granularity. This endpoint is ideal for analyzing market dynamics on an hourly basis, backfilling all trades on an instrument, and compliance or quantitative research.

**Parameters:**

- `market` (query, string, required): The exchange to obtain data from.  
  Example: `coinbase`

- `instrument` (query, string, required): A mapped and/or unmapped instrument to retrieve for a specific market (e.g., `BTC-USD`).  
  Example: `BTC-USD`

- `groups` (query, array of strings, optional): Filter by specific groups of interest.  
  Enum: ID, MAPPING, MAPPING_ADVANCED, TRADE, STATUS  
  Example: `[]`

- `hour_ts` (query, integer, optional): Unix timestamp in seconds for the hour containing the trades you are interested in.  
  Example: `1576771200`

- `apply_mapping` (query, boolean, optional): Determines if provided instrument values are converted according to internal mappings.  
  Default: true  
  Example: `true`

- `response_format` (query, string, optional): Choose the format of the data response from the API.  
  Enum: JSON, CSV  
  Default: JSON  
  Example: `JSON`

- `return_404_on_empty_response` (query, boolean, optional): If true, returns a 404 status code when there are no items; otherwise, returns 200 with an empty array or CSV header.  
  Default: false  
  Example: `false`

- `skip_invalid_messages` (query, boolean, optional): If true, filters out invalid trades from the response.  
  Default: false  
  Example: `false`

**Example Response:**  
```json
  {
    Data: [
      {
        TYPE: "952"
        MARKET: "coinbase"
        INSTRUMENT: "BTC-USD"
        MAPPED_INSTRUMENT: "BTC-USD"
        BASE: "BTC"
        QUOTE: "USD"
        SIDE: "BUY"
        ID: "79832953"
        TIMESTAMP: 1576771201
        TIMESTAMP_NS: 315000000
        RECEIVED_TIMESTAMP: 1644935374
        RECEIVED_TIMESTAMP_NS: 67000000
        QUANTITY: 0.07402902
        PRICE: 7136
        QUOTE_QUANTITY: 528.27108672
        SOURCE: "POLLING"
        CCSEQ: 
        79832951
      },
    ]
    Err: {}
  }
```
---

## `/spot/v2/historical/trades`

**Description:**  
This endpoint provides detailed, standardized, and deduplicated trade data for a specified instrument on a chosen exchange, starting from a given timestamp. It captures every transaction executed, detailing each trade's timestamp, transaction value, quantity, and associated market. Each trade includes an individual CCSEQ (CryptoCompare Sequence) number, trade side, and both received (by us) and reported (by the exchange) timestamps with nanosecond granularity. This endpoint is ideal for analyzing specific periods of trading activity in granular detail and for staying up to date with the latest spot trades.

**Parameters:**

- `market` (query, string, required): The exchange to obtain data from.  
  Example: `coinbase`

- `instrument` (query, string, required): A mapped and/or unmapped instrument to retrieve for a specific market (e.g., `BTC-USD`).  
  Example: `BTC-USD`

- `groups` (query, array of strings, optional): Filter by specific groups of interest.  
  Enum: ID, MAPPING, MAPPING_ADVANCED, TRADE, STATUS  
  Example: `[]`

- `after_ts` (query, integer, required): Unix timestamp in seconds of the earliest trade in the response.  
  Example: `1576774145`

- `last_ccseq` (query, integer, optional): Helps paginate messages within the same second.  
  Default: 0  
  Example: `0`

- `limit` (query, integer, optional): The maximum number of trades to return.  
  Default: 100, Min: 1, Max: 5000  
  Example: `100`

- `apply_mapping` (query, boolean, optional): Determines if provided instrument values are converted according to internal mappings.  
  Default: true  
  Example: `true`

- `response_format` (query, string, optional): Choose the format of the data response from the API.  
  Enum: JSON, CSV  
  Default: JSON  
  Example: `JSON`

- `skip_invalid_messages` (query, boolean, optional): If true, filters out invalid trades from the response.  
  Default: false  
  Example: `false`

**Example Response:**  
```json
  {
    Data: [
      {
        TYPE: "952"
        MARKET: "coinbase"
        INSTRUMENT: "BTC-USD"
        MAPPED_INSTRUMENT: "BTC-USD"
        BASE: "BTC"
        QUOTE: "USD"
        SIDE: "SELL"
        ID: "79835283"
        TIMESTAMP: 1576774145
        TIMESTAMP_NS: 755000000
        RECEIVED_TIMESTAMP: 1644935388
        RECEIVED_TIMESTAMP_NS: 84000000
        QUANTITY: 0.00168286
        PRICE: 7138.01
        QUOTE_QUANTITY: 12.0122715086
        SOURCE: "POLLING"
        CCSEQ: 79835281
      }
    ]
    Err: {}
  }
```
---

## `/spot/v1/historical/orderbook/l2/metrics/minute`

**Description:**  
This endpoint provides accurate, minute-by-minute market metrics derived from order book snapshots in spot markets. It returns calculated metrics such as the best bid and ask prices, mid-price, spread percentages, and detailed depth and slippage metrics at specific percentage levels. This is ideal for users who need high-resolution and synchronized market data for comprehensive analysis and decision-making.

**Parameters:**

- `market` (query, string, required): The exchange to obtain data from.  
  Example: `coinbase`

- `instrument` (query, string, required): A mapped and/or unmapped instrument to retrieve for a specific market (e.g., `BTC-USD`).  
  Example: `BTC-USD`

- `to_ts` (query, integer, optional): Returns historical data before this unix timestamp.  
  Example: `1622505600`

- `groups` (query, array of strings, optional): Filter by specific groups of interest.  
  Enum: ID, MAPPING, TOP_OF_BOOK, DEPTH_BEST_PRICE, DEPTH_MID_PRICE, SLIPPAGE_BEST_PRICE, SLIPPAGE_MID_PRICE, SLIPPAGE_RAW  
  Example: `[]`

- `depth_percentage_levels` (query, array of strings, optional): Comma separated percentage levels greater than 0, relative to the current market price, to analyze the order book depth.  
  Example: `["0.5", "2", "5"]`

- `depth_measurement_asset` (query, string, optional): Defines the asset in which the depth of the order book is measured.  
  Example: `USD`

- `slippage_size_limits` (query, array of strings, optional): Comma separated trade sizes for which slippage is to be calculated.  
  Example: `["50000", "100000"]`

- `slippage_calculation_asset` (query, string, optional): Specifies the asset in which slippage is calculated.  
  Example: `BTC`

- `limit` (query, integer, optional): The number of data points to return.  
  Default: 5, Min: 1, Max: 60  
  Example: `5`

- `apply_mapping` (query, boolean, optional): Determines if provided instrument values are converted according to internal mappings.  
  Default: true  
  Example: `true`

- `response_format` (query, string, optional): Choose the format of the data response from the API.  
  Enum: JSON, CSV  
  Default: JSON  
  Example: `JSON`

- `return_404_on_empty_response` (query, boolean, optional): If true, returns a 404 status code when there are no items; otherwise, returns 200 with an empty array or CSV header.  
  Default: false  
  Example: `false`

**Example Response:**  
```json
{
    "Data": [
        {
            "UNIT": "MINUTE",
            "TIMESTAMP": 1749152280,
            "TYPE": "961",
            "MARKET": "coinbase",
            "INSTRUMENT": "BTC-USD",
            "CCSEQ": 61799271658,
            "DEPTH_ASSET": "USD",
            "SLIPPAGE_ASSET": "USD",
            "MAPPED_INSTRUMENT": "BTC-USD",
            "BASE": "BTC",
            "QUOTE": "USD",
            "BEST_BID": 102416.66,
            "BEST_BID_QUANTITY": 0.00488201,
            "BEST_ASK": 102416.67,
            "BEST_ASK_QUANTITY": 0.26325252,
            "MID_PRICE": 102416.665,
            "SPREAD_PERCENTAGE": 0.000009764035960358599,
            "SPREAD": 0.01,
            "DEPTH_BEST_PRICE_ASK_0.5_PERCENT": 15576595.604295967,
            "DEPTH_BEST_PRICE_ASK_2_PERCENT": 21060785.49046703,
            "DEPTH_BEST_PRICE_ASK_5_PERCENT": 35587337.626732625,
            "DEPTH_BEST_PRICE_BID_0.5_PERCENT": 17539459.41136568,
            "DEPTH_BEST_PRICE_BID_2_PERCENT": 31958311.927735828,
            "DEPTH_BEST_PRICE_BID_5_PERCENT": 66205245.571046,
            "DEPTH_MID_PRICE_ASK_0.5_PERCENT": 15576595.604295967,
            "DEPTH_MID_PRICE_ASK_2_PERCENT": 21060785.49046703,
            "DEPTH_MID_PRICE_ASK_5_PERCENT": 35587337.626732625,
            "DEPTH_MID_PRICE_BID_0.5_PERCENT": 17539459.41136568,
            "DEPTH_MID_PRICE_BID_2_PERCENT": 31958311.927735828,
            "DEPTH_MID_PRICE_BID_5_PERCENT": 66205245.571046,
            "SLIPPAGE_BEST_PRICE_AVG_ASK_50000": 0.002879915348570287,
            "SLIPPAGE_BEST_PRICE_AVG_BID_50000": 0.010076826145057163,
            "SLIPPAGE_BEST_PRICE_AVG_ASK_100000": 0.00557644468814943,
            "SLIPPAGE_BEST_PRICE_AVG_BID_100000": 0.014091330749336021,
            "SLIPPAGE_BEST_PRICE_MAX_ASK_50000": 0.007157038009534971,
            "SLIPPAGE_BEST_PRICE_MAX_BID_50000": 0.01798535511702881,
            "SLIPPAGE_BEST_PRICE_MAX_ASK_100000": 0.011834011006216078,
            "SLIPPAGE_BEST_PRICE_MAX_BID_100000": 0.01871765784980686,
            "SLIPPAGE_MID_PRICE_AVG_ASK_50000": 0.0028847975071484514,
            "SLIPPAGE_MID_PRICE_AVG_BID_50000": 0.010081707671084877,
            "SLIPPAGE_MID_PRICE_AVG_ASK_100000": 0.005581326978372642,
            "SLIPPAGE_MID_PRICE_AVG_BID_100000": 0.0140962120793749,
            "SLIPPAGE_MID_PRICE_MAX_ASK_50000": 0.007161920376923033,
            "SLIPPAGE_MID_PRICE_MAX_BID_50000": 0.01799023625696072,
            "SLIPPAGE_MID_PRICE_MAX_ASK_100000": 0.011838893601934802,
            "SLIPPAGE_MID_PRICE_MAX_BID_100000": 0.018722538953987615,
            "SLIPPAGE_RAW_AVG_ASK_50000": 102419.61951339882,
            "SLIPPAGE_RAW_AVG_BID_50000": 102406.33965122822,
            "SLIPPAGE_RAW_AVG_ASK_100000": 102422.381208954,
            "SLIPPAGE_RAW_AVG_BID_100000": 102402.22812969697,
            "SLIPPAGE_RAW_MAX_ASK_50000": 102424,
            "SLIPPAGE_RAW_MAX_BID_50000": 102398.24,
            "SLIPPAGE_RAW_MAX_ASK_100000": 102428.79,
            "SLIPPAGE_RAW_MAX_BID_100000": 102397.49
        }
    ],
    "Warn": {},
    "Err": {}
}
```
---

## `/spot/v2/historical/orderbook/l2/snapshots/minute`

**Description:**  
This endpoint provides minute-by-minute Level 2 order book snapshots for specified markets and instruments. Each snapshot includes all bids and asks updated to the zeroth nanosecond, detailing prices, quantities, and precise timestamps of last updates at the nanosecond level. This supports precise market analysis and allows for consistent and accurate cross-market comparison at identical nanosecond intervals.

**Parameters:**

- `market` (query, string, required): The exchange to obtain data from.  
  Example: `coinbase`

- `instrument` (query, string, required): A mapped and/or unmapped instrument to retrieve for a specific market (e.g., `BTC-USD`).  
  Example: `BTC-USD`

- `limit` (query, integer, optional): The number of data points to return.  
  Default: 5, Min: 1, Max: 60  
  Example: `5`

- `to_ts` (query, integer, optional): Returns historical data before this unix timestamp.  
  Example: `1622505600`

- `depth` (query, integer, optional): The number of top bids and asks to return.  
  Default: 100, Min: 1, Max: 25000  
  Example: `100`

- `apply_mapping` (query, boolean, optional): Determines if provided instrument values are converted according to internal mappings.  
  Default: true  
  Example: `true`

- `response_format` (query, string, optional): Choose the format of the data response from the API.  
  Enum: JSON, CSV  
  Default: JSON  
  Example: `JSON`

- `return_404_on_empty_response` (query, boolean, optional): If true, returns a 404 status code when there are no items; otherwise, returns 200 with an empty array or CSV header.  
  Default: false  
  Example: `false`

**Example Response:**  
```json
{
    "Data": [
        {
            "UNIT": "MINUTE",
            "TIMESTAMP": 1749152400,
            "TYPE": "957",
            "MARKET": "coinbase",
            "INSTRUMENT": "BTC-USD",
            "CCSEQ": 61799375014,
            "MAPPED_INSTRUMENT": "BTC-USD",
            "BASE": "BTC",
            "QUOTE": "USD",
            "TOTAL_AVAILABLE_ASKS": 20095,
            "TOTAL_AVAILABLE_BIDS": 24570,
            "ASKS": [
                {
                    "PRICE": 102340.01,
                    "QUANTITY": 0.34030682,
                    "LAST_UPDATE": 1749152399,
                    "LAST_UPDATE_NS": 892966000
                },

            ],
            "BIDS": [
                {
                    "PRICE": 102340,
                    "QUANTITY": 0.01669554,
                    "LAST_UPDATE": 1749152399,
                    "LAST_UPDATE_NS": 843765000
                },
            ]
        }
    ],
    "Err": {}
}
```
---

## `/spot/v1/historical/orderbook/l2/consolidated/metrics/minute`

**Description:**  
This endpoint provides aggregated, minute-by-minute market metrics for a single instrument across multiple spot markets. It consolidates data from various markets, offering a comprehensive view of market activity, including aggregated best bid and ask prices, mid-price, spread percentages, and combined depth and slippage metrics at specific percentage levels. This enables precise cross-market comparisons and is ideal for high-resolution, multi-market synchronized analysis.

**Parameters:**

- `instrument` (query, string, required): The mapped instrument to retrieve on specific or all available markets.  
  Example: `BTC-USD`

- `markets` (query, array of strings, required): The exchanges to obtain data from.  
  Example: `["kraken", "coinbase"]`

- `to_ts` (query, integer, optional): Returns historical data before this unix timestamp.  
  Example: `1622505600`

- `groups` (query, array of strings, optional): Filter by specific groups of interest.  
  Enum: ID, MAPPING, TOP_OF_BOOK, DEPTH_BEST_PRICE, DEPTH_MID_PRICE, SLIPPAGE_BEST_PRICE, SLIPPAGE_MID_PRICE, SLIPPAGE_RAW  
  Example: `[]`

- `depth_percentage_levels` (query, array of strings, optional): Comma separated percentage levels greater than 0, relative to the current market price, to analyze the order book depth.  
  Example: `["0.5", "2", "5"]`

- `depth_measurement_asset` (query, string, optional): Defines the asset in which the depth of the order book is measured.  
  Example: `USD`

- `slippage_size_limits` (query, array of strings, optional): Comma separated trade sizes for which slippage is to be calculated.  
  Example: `["100000", "500000", "1000000"]`

- `slippage_calculation_asset` (query, string, optional): Specifies the asset in which slippage is calculated.  
  Example: `BTC`

- `limit` (query, integer, optional): The number of data points to return.  
  Default: 5, Min: 1, Max: 60  
  Example: `5`

- `response_format` (query, string, optional): Choose the format of the data response from the API.  
  Enum: JSON, CSV  
  Default: JSON  
  Example: `JSON`

- `return_404_on_empty_response` (query, boolean, optional): If true, returns a 404 status code when there are no items; otherwise, returns 200 with an empty array or CSV header.  
  Default: false  
  Example: `false`

**Example Response:**  
```json
{
    "Data": [
        {
            "UNIT": "MINUTE",
            "TIMESTAMP": 1749153240,
            "TYPE": "1521",
            "CONSOLIDATED_ORDER_BOOKS": [
                {
                    "MARKET": "kraken",
                    "INSTRUMENT": "XXBTZUSD",
                    "CCSEQ": 9220777878
                },
                {
                    "MARKET": "coinbase",
                    "INSTRUMENT": "BTC-USD",
                    "CCSEQ": 61800190750
                }
            ],
            "DEPTH_ASSET": "USD",
            "SLIPPAGE_ASSET": "USD",
            "MAPPED_INSTRUMENT": "BTC-USD",
            "BASE": "BTC",
            "QUOTE": "USD",
            "CONSOLIDATED_BEST_BID": 102097.2,
            "CONSOLIDATED_BEST_BID_QUANTITY": 0.00979,
            "CONSOLIDATED_BEST_BID_MARKET": "kraken",
            "CONSOLIDATED_BEST_ASK": 102056.66,
            "CONSOLIDATED_BEST_ASK_QUANTITY": 0.13169104,
            "CONSOLIDATED_BEST_ASK_MARKET": "coinbase",
            "CONSOLIDATED_MID_PRICE": 102076.93,
            "CONSOLIDATED_SPREAD_PERCENTAGE": -0.039715144254436334,
            "CONSOLIDATED_SPREAD": -40.54,
            "DEPTH_BEST_PRICE_ASK_0.5_PERCENT": 32848121.912482914,
            "DEPTH_BEST_PRICE_ASK_2_PERCENT": 45192600.891864166,
            "DEPTH_BEST_PRICE_ASK_5_PERCENT": 69907908.36574872,
            "DEPTH_BEST_PRICE_BID_0.5_PERCENT": 35272245.22947251,
            "DEPTH_BEST_PRICE_BID_2_PERCENT": 78183363.8238796,
            "DEPTH_BEST_PRICE_BID_5_PERCENT": 130892227.96292855,
            "DEPTH_MID_PRICE_ASK_0.5_PERCENT": 32907735.482038155,
            "DEPTH_MID_PRICE_ASK_2_PERCENT": 46323592.55790842,
            "DEPTH_MID_PRICE_ASK_5_PERCENT": 69944486.49673395,
            "DEPTH_MID_PRICE_BID_0.5_PERCENT": 35390471.01379903,
            "DEPTH_MID_PRICE_BID_2_PERCENT": 78316255.72381084,
            "DEPTH_MID_PRICE_BID_5_PERCENT": 130901938.88629699,
            "SLIPPAGE_BEST_PRICE_AVG_ASK_100000": 0.009449361750556225,
            "SLIPPAGE_BEST_PRICE_AVG_BID_100000": 0.04590612919928049,
            "SLIPPAGE_BEST_PRICE_AVG_ASK_500000": 0.015817938055028298,
            "SLIPPAGE_BEST_PRICE_AVG_BID_500000": 0.04754295982379951,
            "SLIPPAGE_BEST_PRICE_AVG_ASK_1000000": 0.020332402955129187,
            "SLIPPAGE_BEST_PRICE_AVG_BID_1000000": 0.05063640889223507,
            "SLIPPAGE_BEST_PRICE_MAX_ASK_100000": 0.015030866187468805,
            "SLIPPAGE_BEST_PRICE_MAX_BID_100000": 0.04672018429496597,
            "SLIPPAGE_BEST_PRICE_MAX_ASK_500000": 0.018950257631398088,
            "SLIPPAGE_BEST_PRICE_MAX_BID_500000": 0.04877704775449278,
            "SLIPPAGE_BEST_PRICE_MAX_ASK_1000000": 0.03519613516648497,
            "SLIPPAGE_BEST_PRICE_MAX_BID_1000000": 0.05396817934282233,
            "SLIPPAGE_MID_PRICE_AVG_ASK_100000": 0.010410086790487121,
            "SLIPPAGE_MID_PRICE_AVG_BID_100000": 0.02605767291477888,
            "SLIPPAGE_MID_PRICE_AVG_ASK_500000": 0.004042775130648186,
            "SLIPPAGE_MID_PRICE_AVG_BID_500000": 0.027694828574119767,
            "SLIPPAGE_MID_PRICE_AVG_ASK_1000000": 0.0004707933063290089,
            "SLIPPAGE_MID_PRICE_AVG_BID_1000000": 0.030788891926435316,
            "SLIPPAGE_MID_PRICE_MAX_ASK_100000": 0.004829690704843886,
            "SLIPPAGE_MID_PRICE_MAX_BID_100000": 0.026871889662042146,
            "SLIPPAGE_MID_PRICE_MAX_ASK_500000": 0.0009110775568975281,
            "SLIPPAGE_MID_PRICE_MAX_BID_500000": 0.028929161564713986,
            "SLIPPAGE_MID_PRICE_MAX_ASK_1000000": 0.015331573941340125,
            "SLIPPAGE_MID_PRICE_MAX_BID_1000000": 0.03412132398574291,
            "SLIPPAGE_RAW_AVG_ASK_100000": 102066.30370299393,
            "SLIPPAGE_RAW_AVG_BID_100000": 102050.33112745915,
            "SLIPPAGE_RAW_AVG_ASK_500000": 102072.80325925983,
            "SLIPPAGE_RAW_AVG_BID_500000": 102048.65996922278,
            "SLIPPAGE_RAW_AVG_ASK_1000000": 102077.41057135374,
            "SLIPPAGE_RAW_AVG_BID_1000000": 102045.50164434047,
            "SLIPPAGE_RAW_MAX_ASK_100000": 102072,
            "SLIPPAGE_RAW_MAX_BID_100000": 102049.5,
            "SLIPPAGE_RAW_MAX_ASK_500000": 102076,
            "SLIPPAGE_RAW_MAX_BID_500000": 102047.4,
            "SLIPPAGE_RAW_MAX_ASK_1000000": 102092.58,
            "SLIPPAGE_RAW_MAX_BID_1000000": 102042.1
        }
    ],
    "Warn": {},
    "Err": {}
}
```
---

## `/spot/v1/historical/orderbook/l2/consolidated/snapshots/minute`

**Description:**  
This endpoint provides minute-by-minute Level 2 order book snapshots for a specified instrument across multiple markets. Each snapshot includes all bids and asks updated to the zeroth nanosecond, detailing prices, quantities, and precise timestamps of the last updates at the nanosecond level for each market. This enables detailed cross-market analysis and comparison at identical nanosecond intervals, offering a unified view of an instrument’s behavior across different exchanges.

**Parameters:**

- `instrument` (query, string, required): The mapped instrument to retrieve on specific or all available markets.  
  Example: `BTC-USD`

- `markets` (query, array of strings, required): The exchanges to obtain data from.  
  Example: `["kraken", "coinbase"]`

- `limit` (query, integer, optional): The number of data points to return.  
  Default: 5, Min: 1, Max: 60  
  Example: `5`

- `to_ts` (query, integer, optional): Returns historical data before this unix timestamp.  
  Example: `1622505600`

- `depth` (query, integer, optional): The number of top bids and asks to return.  
  Default: 100, Min: 1, Max: 25000  
  Example: `100`

- `apply_mapping` (query, boolean, optional): Determines if provided instrument values are converted according to internal mappings.  
  Default: true  
  Example: `true`

- `response_format` (query, string, optional): Choose the format of the data response from the API.  
  Enum: JSON, CSV  
  Default: JSON  
  Example: `JSON`

- `return_404_on_empty_response` (query, boolean, optional): If true, returns a 404 status code when there are no items; otherwise, returns 200 with an empty array or CSV header.  
  Default: false  
  Example: `false`

**Example Response:**  
```json
{
    "Data": [
        {
            "UNIT": "MINUTE",
            "TIMESTAMP": 1749153600,
            "TYPE": "1520",
            "CONSOLIDATED_ORDER_BOOKS": [
                {
                    "MARKET": "kraken",
                    "INSTRUMENT": "XXBTZUSD",
                    "CCSEQ": 9220843629
                },
                {
                    "MARKET": "coinbase",
                    "INSTRUMENT": "BTC-USD",
                    "CCSEQ": 61800510909
                }
            ],
            "MAPPED_INSTRUMENT": "BTC-USD",
            "BASE": "BTC",
            "QUOTE": "USD",
            "TOTAL_AVAILABLE_ASKS": 21359,
            "TOTAL_AVAILABLE_BIDS": 25789,
            "ASKS": [
                {
                    "MARKET": "kraken",
                    "PRICE": 101900.1,
                    "QUANTITY": 0.028,
                    "LAST_UPDATE": 1749153599,
                    "LAST_UPDATE_NS": 505761000
                },
            ],
            "BIDS": [
                {
                    "MARKET": "coinbase",
                    "PRICE": 101917.65,
                    "QUANTITY": 0.02071731,
                    "LAST_UPDATE": 1749153599,
                    "LAST_UPDATE_NS": 969207000
                },
            ]
        }
    ],
    "Warn": {},
    "Err": {}
}
```
---

## `/spot/v1/latest/instrument/metadata`

**Description:**  
This endpoint delivers vital metadata about financial instruments traded on specified exchanges, focusing solely on non-price related information. It provides a comprehensive dataset that includes mappings, operational statuses, and historical data (first seen/last seen timestamps) about each instrument. This is essential for internal data management, compliance, advanced research, and integration.

**Parameters:**

- `market` (query, string, required): The exchange to obtain data from.  
  Example: `coinbase`

- `instruments` (query, array of strings, required): A comma separated array of mapped and/or unmapped instruments to retrieve for a specific market (e.g., `BTC-USD`, `ETH-USD`).  
  Example: `["BTC-USD", "ETH-USD"]`

- `groups` (query, array of strings, optional): Filter by specific groups of interest.  
  Enum: STATUS, INTERNAL, GENERAL, MIGRATION, SOURCE  
  Example: `[]`

- `apply_mapping` (query, boolean, optional): Determines if provided instrument values are converted according to internal mappings.  
  Default: true  
  Example: `true`

**Example Response:**  
```json
{
    "Data": {
        "BTC-USD": {
            "METADATA_VERSION": 8,
            "INSTRUMENT_STATUS": "ACTIVE",
            "FIRST_SEEN_ON_POLLING_TS": 1642010178,
            "LAST_SEEN_ON_POLLING_TS": 1749153834,
            "INSTRUMENT": "BTC-USD",
            "INSTRUMENT_MAPPING": {
                "MAPPED_INSTRUMENT": "BTC-USD",
                "BASE": "BTC",
                "BASE_ID": 1,
                "QUOTE": "USD",
                "QUOTE_ID": 5,
                "TRANSFORM_FUNCTION": "",
                "CREATED_ON": 1646858939
            },
            "INSTRUMENT_EXTERNAL_DATA": "{\"id\":\"BTC-USD\",\"base_currency\":\"BTC\",\"quote_currency\":\"USD\",\"quote_increment\":\"0.01\",\"base_increment\":\"0.00000001\",\"display_name\":\"BTC-USD\",\"min_market_funds\":\"1\",\"margin_enabled\":false,\"post_only\":false,\"limit_only\":false,\"cancel_only\":false,\"status\":\"online\",\"status_message\":\"\",\"trading_disabled\":false,\"fx_stablecoin\":false,\"max_slippage_percentage\":\"0.02000000\",\"auction_mode\":false,\"high_bid_limit_percentage\":\"\"}",
            "INSTRUMENT_AVAILABLE_ON_INSTRUMENTS_ENDPOINT": true,
            "FIRST_OB_L2_MINUTE_SNAPSHOT_TS": 1716546360
        }
    },
    "Err": {}
}
```
---

## `/spot/v1/markets`

**Description:**  
This endpoint provides comprehensive information about various cryptocurrency spot markets. By specifying a market through the `market` parameter, users can retrieve details about a specific market, such as its trading pairs, volume, operational status, and other relevant metadata. If no specific market is indicated, the endpoint delivers data on all available markets. This is essential for market analysis, strategic planning, and decision-making.

**Parameters:**

- `market` (query, string, optional): The exchange to obtain data from.  
  Example: `kraken`

**Example Response:**  
```json
{
    "Data": {
        "kraken": {
            "TYPE": "602",
            "EXCHANGE_STATUS": "ACTIVE",
            "MAPPED_INSTRUMENTS_TOTAL": 1154,
            "UNMAPPED_INSTRUMENTS_TOTAL": 96,
            "INSTRUMENT_STATUS": {
                "ACTIVE": 1042,
                "IGNORED": 0,
                "RETIRED": 132,
                "EXPIRED": 0,
                "RETIRED_UNMAPPED": 76
            },
            "TOTAL_TRADES_SPOT": 1379154158,
            "HAS_ORDERBOOK_L2_MINUTE_SNAPSHOTS_ENABLED": true
        }
    },
    "Err": {}
}
```
---

## `/spot/v1/markets/instruments`

**Description:**  
This endpoint retrieves a comprehensive dictionary of mapped instruments across one or more spot markets, filtered by a specified state or status. Each entry uses the instrument ID—standardized by the mapping team—as the key, ensuring consistency and ease of reference. This is ideal for applications that depend on uniform identifiers to integrate and interpret market data effectively.

**Parameters:**

- `market` (query, string, optional): The exchange to obtain data from.  
  Example: `kraken`

- `instruments` (query, array of strings, optional): The mapped instruments to retrieve on a specific market or all available markets.  
  Example: `["BTC-USD", "ETH-USD"]`

- `instrument_status` (query, array of strings, optional): The current state of an instrument.  
  Enum: ACTIVE, IGNORED, RETIRED, EXPIRED, READY_FOR_DECOMMISSIONING, RETIRED_UNMAPPED  
  Default: ["ACTIVE"]  
  Example: `["ACTIVE"]`

**Example Response:**  
```json
{
    "Data": {
        "kraken": {
            "TYPE": "602",
            "EXCHANGE_STATUS": "ACTIVE",
            "MAPPED_INSTRUMENTS_TOTAL": 1154,
            "UNMAPPED_INSTRUMENTS_TOTAL": 96,
            "INSTRUMENT_STATUS": {
                "ACTIVE": 1042,
                "IGNORED": 0,
                "RETIRED": 132,
                "EXPIRED": 0,
                "RETIRED_UNMAPPED": 76
            },
            "TOTAL_TRADES_SPOT": 1379183049,
            "HAS_ORDERBOOK_L2_MINUTE_SNAPSHOTS_ENABLED": true,
            "instruments": {
                "BTC-USD": {
                    "TYPE": "612",
                    "INSTRUMENT_STATUS": "ACTIVE",
                    "INSTRUMENT": "XXBTZUSD",
                    "HISTO_SHARD": "PG_COLLECT_02",
                    "MAPPED_INSTRUMENT": "BTC-USD",
                    "INSTRUMENT_MAPPING": {
                        "MAPPED_INSTRUMENT": "BTC-USD",
                        "BASE": "BTC",
                        "BASE_ID": 1,
                        "QUOTE": "USD",
                        "QUOTE_ID": 5,
                        "TRANSFORM_FUNCTION": "",
                        "CREATED_ON": 1646923899
                    },
                    "HAS_TRADES_SPOT": true,
                    "FIRST_TRADE_SPOT_TIMESTAMP": 1381095255,
                    "LAST_TRADE_SPOT_TIMESTAMP": 1749177039,
                    "TOTAL_TRADES_SPOT": 83708262
                }
            }
        }
    },
    "Err": {}
}
```