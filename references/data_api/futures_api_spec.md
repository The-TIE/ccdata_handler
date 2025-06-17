# CryptoCompare "Futures API" Specification

This document outlines the key endpoints, parameters, and example responses for the CryptoCompare "Futures API" used in this project.

---
## `/futures/v1/markets`

**Description:**  
This endpoint provides comprehensive information about various cryptocurrency futures markets. By utilizing the `market` parameter, users can access detailed data about specific futures markets, including trading pairs, volume, operational status, and additional relevant metadata. If no specific market is specified, the endpoint returns information on all available futures markets. This capability is crucial for users who wish to explore and analyze the characteristics and trading conditions of different cryptocurrency futures exchanges or market segments, aiding in market analysis, strategic planning, and decision-making.

**Parameters:**

- `market` (query, string, optional): The exchange to obtain data from.  
  Example: `binance`

- `groups` (query, array of strings, optional): When requesting market metadata entries you can filter by specific groups of interest. To do so just pass the groups of interest into the URL as a comma separated list. If left empty it will get all data that your account is allowed to access.  
  Allowed values:  
  - ID  
  - INSTRUMENT_SUMMARY  
  - BASIC  
  - INTERNAL  
  - RESOURCE_LINKS  
  - DESCRIPTION  
  - DESCRIPTION_SUMMARY  
  - INTEGRATION_FUTURES  
  Default: `[]`  
  Example: `[]`

**Example Response:**  
```json
{
    "Data": {
        "binance": {
            "ID": 8,
            "TYPE": "604",
            "EXCHANGE_STATUS": "ACTIVE",
            "EXCHANGE_INTERNAL_NAME": "binance",
            "URI": "binance",
            "MAPPED_INSTRUMENTS_TOTAL": 751,
            "UNMAPPED_INSTRUMENTS_TOTAL": 35,
            "INSTRUMENT_STATUS": {
                "ACTIVE": 523,
                "IGNORED": 0,
                "RETIRED": 100,
                "EXPIRED": 145,
                "RETIRED_UNMAPPED": 18
            },
            "TOTAL_TRADES_FUTURES": 131986387884,
            "TOTAL_OPEN_INTEREST_UPDATES": 1524415263,
            "TOTAL_FUNDING_RATE_UPDATES": 51374919,
            "HAS_ORDERBOOK_L2_MINUTE_SNAPSHOTS_ENABLED": true,
            "CREATED_ON": 1709305140,
            "UPDATED_ON": 1749660760,
            "NAME": "Binance",
            "LOGO_URL": "https://resources.cryptocompare.com/exchange-management/8/1709630578537.png",
            "LAUNCH_DATE": 1499990400,
            "HAS_SPOT_TRADING": true,
            "HAS_FUTURES_TRADING": true,
            "HAS_INDEX_PUBLISHING": true,
            "HAS_OPTIONS_TRADING": true,
            "HAS_DEX_TRADING": false,
            "EXCHANGE_DESCRIPTION_SNIPPET": "Founded in 2017 by CZ, Binance ...",
            "FUTURES_TRADING_LAUNCH_DATE": 1567900800,
            "FUTURES_TRADING_MECHANISMS": [
                {
                    "NAME": "ORDER_BOOK"
                }
            ],
            "HAS_PERPETUAL_CONTRACTS": true,
            "FUTURES_SETTLEMENT_TYPES": [
                {
                    "NAME": "CASH_SETTLEMENT"
                }
            ],
            "FUTURES_DENOMINATION_TYPES": [
                {
                    "NAME": "VANILLA"
                },
                {
                    "NAME": "INVERSE"
                }
            ],
            "EXCHANGE_DESCRIPTION": "## Founding and History\nBinance, established in 2017...",
            "EXCHANGE_DESCRIPTION_SUMMARY": "Binance, founded in 2017 by Changpeng Zhao...",
            "WEBSITE_URL": "https://www.binance.com",
            "BLOG_URL": "https://www.binance.com/en/blog",
            "FUTURES_INTEGRATION_COMMENTS": "# Orderbook\n* Hybrid Integration: Websocket Updates and REST Snapshots (comment added: 2024-07-03)",
            "FUTURES_TRADES_INTEGRATION_STAGE": "IN_PRODUCTION",
            "FUTURES_TRADES_INTEGRATION_DATE": 1640995200,
            "HAS_FUTURES_TRADES_POLLING_BACKFILL": false,
            "FUTURES_FUNDING_RATE_INTEGRATION_STAGE": "IN_PRODUCTION",
            "FUTURES_FUNDING_RATE_INTEGRATION_DATE": 1640995200,
            "FUTURES_OPEN_INTEREST_INTEGRATION_STAGE": "IN_PRODUCTION",
            "FUTURES_OPEN_INTEREST_INTEGRATION_DATE": 1640995200,
            "FUTURES_INDEX_INTEGRATION_STAGE": "IN_PRODUCTION",
            "FUTURES_INDEX_INTEGRATION_DATE": 1640995200
        },
        "bit": {
            "ID": 37,
            "TYPE": "604",
            "EXCHANGE_STATUS": "ACTIVE",
            "EXCHANGE_INTERNAL_NAME": "bit",
            "URI": "bit",
            "MAPPED_INSTRUMENTS_TOTAL": 108,
            "UNMAPPED_INSTRUMENTS_TOTAL": 21,
            "INSTRUMENT_STATUS": {
                "ACTIVE": 124,
                "IGNORED": 0,
                "RETIRED": 1,
                "EXPIRED": 0,
                "RETIRED_UNMAPPED": 4
            },
            "TOTAL_TRADES_FUTURES": 38085315,
            "TOTAL_OPEN_INTEREST_UPDATES": 149034491,
            "TOTAL_FUNDING_RATE_UPDATES": 92893255,
            "HAS_ORDERBOOK_L2_MINUTE_SNAPSHOTS_ENABLED": false,
            "CREATED_ON": 1709391455,
            "UPDATED_ON": 1749660761,
            "NAME": "BIT",
            "LOGO_URL": "https://resources.cryptocompare.com/exchange-management/37/1709716415495.png",
            "LAUNCH_DATE": 1596240000,
            "HAS_SPOT_TRADING": true,
            "HAS_FUTURES_TRADING": true,
            "HAS_INDEX_PUBLISHING": true,
            "HAS_OPTIONS_TRADING": true,
            "HAS_DEX_TRADING": false,
            "EXCHANGE_DESCRIPTION_SNIPPET": "BIT.com, launched by Matrixport in 2020, swiftly grew to offer a wide range of crypto trading options including BCH, ETH, and USD-margined futures, enhancing its global market presence.",
            "FUTURES_TRADING_LAUNCH_DATE": 1596240000,
            "HAS_PERPETUAL_CONTRACTS": true,
            "EXCHANGE_DESCRIPTION": "## Founding and History\nBIT.com was launched in August 2020...",
            "EXCHANGE_DESCRIPTION_SUMMARY": "BIT.com, launched in August 2020 as a spinoff from Matrixport...",
            "WEBSITE_URL": "https://www.bit.com/",
            "BLOG_URL": "https://blog.bit.com/",
            "FUTURES_TRADES_INTEGRATION_STAGE": "BACKLOG",
            "FUTURES_FUNDING_RATE_INTEGRATION_STAGE": "BACKLOG",
            "FUTURES_OPEN_INTEREST_INTEGRATION_STAGE": "BACKLOG",
            "FUTURES_INDEX_INTEGRATION_STAGE": "RESEARCH",
            "FUTURES_ORDER_BOOK_INTEGRATION_STAGE": "RESEARCH"
        }
    },
    "Err": {}
}
```
---
## `/futures/v1/markets/instruments`

**Description:**  
This endpoint retrieves a comprehensive dictionary of mapped instruments across one or more futures markets, filtered by specified states or statuses. Each entry in the dictionary uses the instrument ID—standardized by the mapping team—as the key, ensuring consistency and ease of reference. This endpoint is particularly valuable for users needing precise and standardized information on trading instruments, facilitating the tracking, comparison, and analysis of different instruments within and across various futures markets. It is ideal for applications that depend on uniform identifiers to integrate and interpret market data effectively.

**Parameters:**

- `market` (query, string, optional): The exchange to obtain data from.  
  Example: `kraken`

- `instruments` (query, array of strings, optional): The mapped instruments to retrieve on a specific market or all available markets.  
  Default: `[]`  
  Example: `["BTC-USD-INVERSE-PERPETUAL", "ETH-USD-INVERSE-PERPETUAL"]`

- `instrument_status` (query, array of strings, optional): The current state of an instrument, indicating whether it is actively traded or in another status.  
  Allowed values:  
  - ACTIVE  
  - IGNORED  
  - RETIRED  
  - EXPIRED  
  - READY_FOR_DECOMMISSIONING  
  - RETIRED_UNMAPPED  
  Default: `["ACTIVE"]`  
  Example: `["ACTIVE"]`

- `groups` (query, array of strings, optional): When requesting market metadata entries you can filter by specific groups of interest. To do so just pass the groups of interest into the URL as a comma separated list. If left empty it will get all data that your account is allowed to access.  
  Allowed values:  
  - ID  
  - INSTRUMENT_SUMMARY  
  - BASIC  
  - INTERNAL  
  - RESOURCE_LINKS  
  - DESCRIPTION  
  - DESCRIPTION_SUMMARY  
  - INTEGRATION_FUTURES  
  Default: `[]`  
  Example: `[]`

**Example Response:**  
```json
{
    "Data": {
        "binance": {
            "ID": 8,
            "TYPE": "604",
            "EXCHANGE_STATUS": "ACTIVE",
            "EXCHANGE_INTERNAL_NAME": "binance",
            "URI": "binance",
            "MAPPED_INSTRUMENTS_TOTAL": 754,
            "UNMAPPED_INSTRUMENTS_TOTAL": 32,
            "INSTRUMENT_STATUS": {
                "ACTIVE": 523,
                "IGNORED": 0,
                "RETIRED": 100,
                "EXPIRED": 145,
                "RETIRED_UNMAPPED": 18
            },
            "TOTAL_TRADES_FUTURES": 132022218083,
            "TOTAL_OPEN_INTEREST_UPDATES": 1524994815,
            "TOTAL_FUNDING_RATE_UPDATES": 52112671,
            "HAS_ORDERBOOK_L2_MINUTE_SNAPSHOTS_ENABLED": true,
            "CREATED_ON": 1709305140,
            "UPDATED_ON": 1749660760,
            "NAME": "Binance",
            "LOGO_URL": "https://resources.cryptocompare.com/exchange-management/8/1709630578537.png",
            "LAUNCH_DATE": 1499990400,
            "HAS_SPOT_TRADING": true,
            "HAS_FUTURES_TRADING": true,
            "HAS_INDEX_PUBLISHING": true,
            "HAS_OPTIONS_TRADING": true,
            "HAS_DEX_TRADING": false,
            "EXCHANGE_DESCRIPTION_SNIPPET": "Founded in 2017 by CZ, Binance quickly rose to prominence in crypto trading. Facing regulatory hurdles and a major hack, it expanded globally and diversified offerings, including NFTs and stablecoins. Leadership changes in 2023.",
            "FUTURES_TRADING_LAUNCH_DATE": 1567900800,
            "FUTURES_TRADING_MECHANISMS": [
                {
                    "NAME": "ORDER_BOOK"
                }
            ],
            "HAS_PERPETUAL_CONTRACTS": true,
            "FUTURES_SETTLEMENT_TYPES": [
                {
                    "NAME": "CASH_SETTLEMENT"
                }
            ],
            "FUTURES_DENOMINATION_TYPES": [
                {
                    "NAME": "VANILLA"
                },
                {
                    "NAME": "INVERSE"
                }
            ],
            "EXCHANGE_DESCRIPTION": "## Founding and History\nBinance, established in 2017 by Changpeng Zhao (CZ), rapidly emerged as a leading figure in the cryptocurrency exchange industry. Leveraging his experience in developing trading software for Bloomberg and contributing to projects like Blockchain.info, CZ launched Binance following a $15 million raise through an initial coin offering (ICO). Starting with a curated selection of cryptocurrencies including Binance Coin (BNB), Bitcoin (BTC), and Ethereum (ETH), Binance swiftly attracted a significant user base, adding around 5,000 users per day in its early stages.\n\nThe platform navigated regulatory challenges, notably China's 2017 cryptocurrency trading crackdown, by relocating out of China. This move highlighted Binance's strategic agility and commitment to maintaining operations amidst regulatory shifts. The decision enabled continuous growth and global expansion, including establishing operations in Malta and Jersey and launching platforms tailored to regions like Uganda.\n\nPartnerships have been instrumental in Binance's growth. Its 2019 collaboration with Simplex facilitated cryptocurrency purchases with credit cards, significantly lowering the entry barriers for new users. However, Binance faced security challenges, including a significant hack in 2019 resulting in a $40 million loss. In response, Binance established the Secure Asset Fund for Users (SAFU) to bolster security and protect user assets.\n\nThrough strategic planning, innovative solutions, and a robust response to regulatory and security challenges, Binance has cemented its status as a dominant player in the cryptocurrency exchange space. Its journey reflects the evolving landscape of digital finance and Binance's pivotal role in the adoption of cryptocurrency trading and blockchain technology.\n\n## Expansive Product Offerings\nBinance's offerings extend beyond spot trading, including:\n\n* **Derivatives Trading:** Supporting a wide range of derivatives products, such as perpetual and quarterly futures, and European-style options, with leverages up to 125x on some markets.\n* **Leveraged Tokens:** Providing traders the ability to take leveraged positions without liquidation risk.\n* **NFT Marketplace:** Launched in June 2021, it hosts a variety of NFTs, enabling users to mint, sell, and purchase digital collectibles.\n* **Binance Convert:** Simplifies exchanging between 350 tokens.\n* **Simple Earn:** Allows users to earn yield on over 300 cryptocurrencies through fixed or flexible staking.\n* **DeFi Staking and Binance Pool:** Facilitates participation in DeFi staking and mining via its mining pool.\n\n## Impactful Milestones and Contributions\nBinance's impact is highlighted by:\n\n* Its 2018 partnership with the Malta Stock Exchange to facilitate security token trading and investments in blockchain initiatives.\n* Overcoming a major security breach in 2019 by utilizing its SAFU to cover the losses.\n* Pioneering in the stablecoin space with the launch of Binance GBP (BGBP) in 2019, Binance's first stablecoin backed by the British pound.\n\n## Points of Interest:\n* **Leadership Change:** In 2023, amid U.S. legal challenges, Changpeng Zhao stepped down, with Richard Teng taking the helm. This leadership transition signifies Binance's navigation through regulatory pressures and its forward-looking stance.\n* **Regulatory Challenges and Compliance:** Binance has addressed various legal and regulatory issues, particularly with the U.S. CFTC and SEC. These encounters have spurred operational and compliance adjustments, reflecting Binance's commitment to regulatory adherence.\n* **Commitment to Philanthropy:** Binance and CZ demonstrate a strong commitment to giving back, with plans to donate a substantial portion of CZ's wealth. This philanthropic vision is part of Binance's broader corporate responsibility efforts, impacting global social issues through the Binance Charity Foundation.",
            "EXCHANGE_DESCRIPTION_SUMMARY": "Binance, founded in 2017 by Changpeng Zhao, quickly became a leading cryptocurrency exchange. Initially raising $15 million through an ICO, it offered a selection of cryptocurrencies, including Binance Coin (BNB). Navigating regulatory challenges like China's 2017 crypto crackdown by relocating, Binance expanded globally, establishing operations in Malta and Jersey. Key partnerships, such as with Simplex in 2019, enabled credit card purchases of cryptocurrencies. Despite facing a $40 million hack in 2019, Binance enhanced user asset protection with the SAFU fund. Its offerings include derivatives trading, leveraged tokens, an NFT marketplace, Binance Convert, Simple Earn, and DeFi staking. Binance has also been a pioneer in the stablecoin space with Binance GBP (BGBP). Leadership changes in 2023, with Richard Teng taking over amidst U.S. legal challenges, mark a new chapter for Binance, reflecting its adaptability and commitment to compliance and philanthropy.",
            "WEBSITE_URL": "https://www.binance.com",
            "BLOG_URL": "https://www.binance.com/en/blog",
            "FUTURES_INTEGRATION_COMMENTS": "# Orderbook\n* Hybrid Integration: Websocket Updates and REST Snapshots (comment added: 2024-07-03)",
            "FUTURES_TRADES_INTEGRATION_STAGE": "IN_PRODUCTION",
            "FUTURES_TRADES_INTEGRATION_DATE": 1640995200,
            "HAS_FUTURES_TRADES_POLLING_BACKFILL": false,
            "FUTURES_FUNDING_RATE_INTEGRATION_STAGE": "IN_PRODUCTION",
            "FUTURES_FUNDING_RATE_INTEGRATION_DATE": 1640995200,
            "FUTURES_OPEN_INTEREST_INTEGRATION_STAGE": "IN_PRODUCTION",
            "FUTURES_OPEN_INTEREST_INTEGRATION_DATE": 1640995200,
            "FUTURES_INDEX_INTEGRATION_STAGE": "IN_PRODUCTION",
            "FUTURES_INDEX_INTEGRATION_DATE": 1640995200,
            "instruments": {
                "BTC-USD-INVERSE-PERPETUAL": {
                    "TYPE": "614",
                    "INSTRUMENT_STATUS": "ACTIVE",
                    "INSTRUMENT": "BTCUSD_PERP",
                    "HISTO_SHARD": "PG_COLLECT_04",
                    "MAPPED_INSTRUMENT": "BTC-USD-INVERSE-PERPETUAL",
                    "INSTRUMENT_MAPPING": {
                        "MAPPED_INSTRUMENT": "BTC-USD-INVERSE-PERPETUAL",
                        "INDEX_UNDERLYING": "BTC",
                        "INDEX_UNDERLYING_ID": 1,
                        "QUOTE_CURRENCY": "USD",
                        "QUOTE_CURRENCY_ID": 5,
                        "SETTLEMENT_CURRENCY": "BTC",
                        "SETTLEMENT_CURRENCY_ID": 1,
                        "CONTRACT_CURRENCY": "USD",
                        "CONTRACT_CURRENCY_ID": 5,
                        "DENOMINATION_TYPE": "INVERSE",
                        "TRANSFORM_FUNCTION": "",
                        "CREATED_ON": 1655731183
                    },
                    "HAS_TRADES_FUTURES": true,
                    "FIRST_TRADE_FUTURES_TIMESTAMP": 1597129351,
                    "LAST_TRADE_FUTURES_TIMESTAMP": 1750120218,
                    "TOTAL_TRADES_FUTURES": 978207479,
                    "HAS_FUNDING_RATE_UPDATES": true,
                    "FIRST_FUNDING_RATE_UPDATE_TIMESTAMP": 1597075200,
                    "LAST_FUNDING_RATE_UPDATE_TIMESTAMP": 1750120219,
                    "TOTAL_FUNDING_RATE_UPDATES": 102510,
                    "HAS_OPEN_INTEREST_UPDATES": true,
                    "FIRST_OPEN_INTEREST_UPDATE_TIMESTAMP": 1643526000,
                    "LAST_OPEN_INTEREST_UPDATE_TIMESTAMP": 1750120208,
                    "TOTAL_OPEN_INTEREST_UPDATES": 3255707,
                    "CONTRACT_EXPIRATION_TS": null
                },
                "ETH-USDT-VANILLA-PERPETUAL": {
                    "TYPE": "614",
                    "INSTRUMENT_STATUS": "ACTIVE",
                    "INSTRUMENT": "ETHUSDT",
                    "HISTO_SHARD": "PG_COLLECT_04",
                    "MAPPED_INSTRUMENT": "ETH-USDT-VANILLA-PERPETUAL",
                    "INSTRUMENT_MAPPING": {
                        "MAPPED_INSTRUMENT": "ETH-USDT-VANILLA-PERPETUAL",
                        "INDEX_UNDERLYING": "ETH",
                        "INDEX_UNDERLYING_ID": 2,
                        "QUOTE_CURRENCY": "USDT",
                        "QUOTE_CURRENCY_ID": 7,
                        "SETTLEMENT_CURRENCY": "USDT",
                        "SETTLEMENT_CURRENCY_ID": 7,
                        "CONTRACT_CURRENCY": "ETH",
                        "CONTRACT_CURRENCY_ID": 2,
                        "DENOMINATION_TYPE": "VANILLA",
                        "TRANSFORM_FUNCTION": "",
                        "CREATED_ON": 1650554410
                    },
                    "HAS_TRADES_FUTURES": true,
                    "FIRST_TRADE_FUTURES_TIMESTAMP": 1574840707,
                    "LAST_TRADE_FUTURES_TIMESTAMP": 1750120250,
                    "TOTAL_TRADES_FUTURES": 5814638478,
                    "HAS_FUNDING_RATE_UPDATES": true,
                    "FIRST_FUNDING_RATE_UPDATE_TIMESTAMP": 1574841600,
                    "LAST_FUNDING_RATE_UPDATE_TIMESTAMP": 1750120243,
                    "TOTAL_FUNDING_RATE_UPDATES": 129842,
                    "HAS_OPEN_INTEREST_UPDATES": true,
                    "FIRST_OPEN_INTEREST_UPDATE_TIMESTAMP": 1643526000,
                    "LAST_OPEN_INTEREST_UPDATE_TIMESTAMP": 1750120246,
                    "TOTAL_OPEN_INTEREST_UPDATES": 6784099,
                    "CONTRACT_EXPIRATION_TS": null
                }
            }
        },
        "bybit": {
            "ID": 5,
            "TYPE": "604",
            "EXCHANGE_STATUS": "ACTIVE",
            "EXCHANGE_INTERNAL_NAME": "bybit",
            "URI": "bybit",
            "MAPPED_INSTRUMENTS_TOTAL": 979,
            "UNMAPPED_INSTRUMENTS_TOTAL": 62,
            "INSTRUMENT_STATUS": {
                "ACTIVE": 625,
                "IGNORED": 0,
                "RETIRED": 69,
                "EXPIRED": 264,
                "RETIRED_UNMAPPED": 83
            },
            "TOTAL_TRADES_FUTURES": 6890172247264350000,
            "TOTAL_OPEN_INTEREST_UPDATES": 4831337630818829000,
            "TOTAL_FUNDING_RATE_UPDATES": 38826277,
            "HAS_ORDERBOOK_L2_MINUTE_SNAPSHOTS_ENABLED": true,
            "CREATED_ON": 1709118990,
            "UPDATED_ON": 1749660760,
            "NAME": "Bybit",
            "LOGO_URL": "https://resources.cryptocompare.com/exchange-management/5/1709119093078.png",
            "LAUNCH_DATE": 1519862400,
            "HAS_SPOT_TRADING": true,
            "HAS_FUTURES_TRADING": true,
            "HAS_INDEX_PUBLISHING": true,
            "HAS_OPTIONS_TRADING": true,
            "HAS_DEX_TRADING": false,
            "EXCHANGE_DESCRIPTION_SNIPPET": "Founded in 2018, Bybit is a leading crypto derivatives exchange known for its perpetual contracts, up to 100x leverage, robust security, and 24/7 support​.",
            "FUTURES_TRADING_LAUNCH_DATE": 1519862400,
            "FUTURES_TRADING_MECHANISMS": [
                {
                    "NAME": "ORDER_BOOK"
                }
            ],
            "HAS_PERPETUAL_CONTRACTS": true,
            "FUTURES_SETTLEMENT_TYPES": [
                {
                    "NAME": "CASH_SETTLEMENT"
                },
                {
                    "NAME": "PHYSICAL_DELIVERY"
                }
            ],
            "FUTURES_DENOMINATION_TYPES": [
                {
                    "NAME": "VANILLA"
                },
                {
                    "NAME": "INVERSE"
                }
            ],
            "EXCHANGE_DESCRIPTION": "## Founding and History\nBybit was founded in March 2018 by a team of experts with deep roots in the finance and technology sectors. With the ambition to blend technological innovation with financial acuity, the platform aimed to offer a reliable and user-friendly environment for leveraged trading enthusiasts. Initially launched with its headquarters in Singapore, Bybit's operational footprint quickly expanded, establishing additional offices in Taiwan, Hong Kong, and the United Kingdom. This rapid growth enabled Bybit to secure a prominent position in the cryptocurrency derivatives market, appealing to a worldwide audience with its comprehensive range of trading products and services​.\n\n## Products Covered\nBeginning with perpetual contracts for Bitcoin and Ethereum, Bybit introduced a trading model that allowed for speculation on cryptocurrency prices without direct ownership of the assets. The platform is notable for supporting up to 100x leverage, thereby magnifying both potential profits and risks. As part of its expansion, Bybit broadened its product suite to include more cryptocurrencies like Ripple, EOS, and Bitcoin Cash, in addition to introducing futures contracts for these assets. The exchange distinguishes itself with a trading engine capable of executing up to 100,000 transactions per second, ensuring rapid trade execution at desired prices. Bybit's interface is engineered to be accessible for all user levels, complemented by competitive fees and high liquidity. The product portfolio has evolved to include innovative features such as grid bot trading on spot markets, copy trading, savings programs, and a marketplace for NFTs, enriching the trading experience and offering multiple streams of potential earnings​.\n\n## Impact and Contributions to the Industry\nBybit has markedly influenced the cryptocurrency derivatives sector through its forward-thinking approach and commitment to an exceptional trading experience. The platform is lauded for its low transaction fees, stringent security protocols, and extensive customer support available round-the-clock in multiple languages. Bybit actively supports the growth of the broader crypto ecosystem through initiatives and partnerships that nurture new projects. With daily trading volumes reaching billions, Bybit's trajectory of growth and influence is keenly observed by traders, investors, and crypto enthusiasts globally. The exchange has played a crucial role in shaping the landscape of cryptocurrency trading, driving innovation and accessibility​.\n\n## Points of Interest\n* **Referral and Learning Initiatives:** Bybit enhances community engagement through a referral program and the Bybit Learning Hub, an educational resource aimed at improving trading proficiency across all skill levels.\n* **Mobile Trading Solutions:** A comprehensive mobile application supports trading on the move, offering full platform functionality, including real-time data and advanced charting.\n* **Robust Security Framework:** Implements top-tier security measures like multi-signature cold wallet storage, two-factor authentication (2FA), SSL encryption, and frequent security reviews to safeguard user assets and data​​.\n* **Competitive and Transparent Fees:** Maintains an attractive fee structure for traders, with no charges on deposits or withdrawals, underscoring its commitment to providing value to its users.",
            "EXCHANGE_DESCRIPTION_SUMMARY": "Bybit, founded in March 2018 by finance and technology veterans, rapidly ascended as a leading cryptocurrency derivatives exchange, initially based in Singapore with expansions to Taiwan, Hong Kong, and the UK. It started with perpetual contracts for Bitcoin and Ethereum, supporting up to 100x leverage, and expanded to include more cryptocurrencies and futures contracts. The platform is praised for its user-friendly interface, high liquidity, and the ability to process up to 100,000 transactions per second. Bybit stands out for its security measures, including multi-signature cold wallet storage and regular audits, alongside 24/7 multilingual customer support. It fosters the crypto community's growth with educational resources through the Bybit Learning Hub and engages users with a referral program. Bybit's offerings have evolved to feature grid bot trading, copy trading, savings programs, NFTs, and more, making significant contributions to the cryptocurrency trading landscape.",
            "WEBSITE_URL": "https://www.bybit.com/",
            "BLOG_URL": "https://blog.bybit.com/",
            "FUTURES_TRADES_INTEGRATION_STAGE": "IN_PRODUCTION",
            "FUTURES_TRADES_INTEGRATION_DATE": 1660608000,
            "HAS_FUTURES_TRADES_POLLING_BACKFILL": true,
            "FUTURES_FUNDING_RATE_INTEGRATION_STAGE": "IN_PRODUCTION",
            "FUTURES_FUNDING_RATE_INTEGRATION_DATE": 1660608000,
            "FUTURES_OPEN_INTEREST_INTEGRATION_STAGE": "IN_PRODUCTION",
            "FUTURES_OPEN_INTEREST_INTEGRATION_DATE": 1660608000,
            "FUTURES_INDEX_INTEGRATION_STAGE": "IN_PRODUCTION",
            "FUTURES_INDEX_INTEGRATION_DATE": 1660608000,
            "FUTURES_ORDER_BOOK_INTEGRATION_STAGE": "IN_PRODUCTION",
            "FUTURES_ORDER_BOOK_INTEGRATION_DATE": 1614816000,
            "instruments": {
                "BTC-USD-INVERSE-PERPETUAL": {
                    "TYPE": "614",
                    "INSTRUMENT_STATUS": "ACTIVE",
                    "INSTRUMENT": "BTCUSD",
                    "HISTO_SHARD": "PG_COLLECT_04",
                    "MAPPED_INSTRUMENT": "BTC-USD-INVERSE-PERPETUAL",
                    "INSTRUMENT_MAPPING": {
                        "MAPPED_INSTRUMENT": "BTC-USD-INVERSE-PERPETUAL",
                        "INDEX_UNDERLYING": "BTC",
                        "INDEX_UNDERLYING_ID": 1,
                        "QUOTE_CURRENCY": "USD",
                        "QUOTE_CURRENCY_ID": 5,
                        "SETTLEMENT_CURRENCY": "BTC",
                        "SETTLEMENT_CURRENCY_ID": 1,
                        "CONTRACT_CURRENCY": "USD",
                        "CONTRACT_CURRENCY_ID": 5,
                        "DENOMINATION_TYPE": "INVERSE",
                        "TRANSFORM_FUNCTION": "",
                        "CREATED_ON": 1670872632
                    },
                    "HAS_TRADES_FUTURES": true,
                    "FIRST_TRADE_FUTURES_TIMESTAMP": 1569888184,
                    "LAST_TRADE_FUTURES_TIMESTAMP": 1750120205,
                    "TOTAL_TRADES_FUTURES": 563103941,
                    "HAS_FUNDING_RATE_UPDATES": true,
                    "FIRST_FUNDING_RATE_UPDATE_TIMESTAMP": 1575676800,
                    "LAST_FUNDING_RATE_UPDATE_TIMESTAMP": 1750120196,
                    "TOTAL_FUNDING_RATE_UPDATES": 129454,
                    "HAS_OPEN_INTEREST_UPDATES": true,
                    "FIRST_OPEN_INTEREST_UPDATE_TIMESTAMP": 1660644503,
                    "LAST_OPEN_INTEREST_UPDATE_TIMESTAMP": 1750120201,
                    "TOTAL_OPEN_INTEREST_UPDATES": 8679332,
                    "CONTRACT_EXPIRATION_TS": null
                },
                "ETH-USDT-VANILLA-PERPETUAL": {
                    "TYPE": "614",
                    "INSTRUMENT_STATUS": "ACTIVE",
                    "INSTRUMENT": "ETHUSDT",
                    "HISTO_SHARD": "PG_COLLECT_04",
                    "MAPPED_INSTRUMENT": "ETH-USDT-VANILLA-PERPETUAL",
                    "INSTRUMENT_MAPPING": {
                        "MAPPED_INSTRUMENT": "ETH-USDT-VANILLA-PERPETUAL",
                        "INDEX_UNDERLYING": "ETH",
                        "INDEX_UNDERLYING_ID": 2,
                        "QUOTE_CURRENCY": "USDT",
                        "QUOTE_CURRENCY_ID": 7,
                        "SETTLEMENT_CURRENCY": "USDT",
                        "SETTLEMENT_CURRENCY_ID": 7,
                        "CONTRACT_CURRENCY": "ETH",
                        "CONTRACT_CURRENCY_ID": 2,
                        "DENOMINATION_TYPE": "VANILLA",
                        "TRANSFORM_FUNCTION": "",
                        "CREATED_ON": 1670872504
                    },
                    "HAS_TRADES_FUTURES": true,
                    "FIRST_TRADE_FUTURES_TIMESTAMP": 1603272200,
                    "LAST_TRADE_FUTURES_TIMESTAMP": 1750120206,
                    "TOTAL_TRADES_FUTURES": 940962973,
                    "HAS_FUNDING_RATE_UPDATES": true,
                    "FIRST_FUNDING_RATE_UPDATE_TIMESTAMP": 1615766400,
                    "LAST_FUNDING_RATE_UPDATE_TIMESTAMP": 1750120196,
                    "TOTAL_FUNDING_RATE_UPDATES": 128203,
                    "HAS_OPEN_INTEREST_UPDATES": true,
                    "FIRST_OPEN_INTEREST_UPDATE_TIMESTAMP": 1660644503,
                    "LAST_OPEN_INTEREST_UPDATE_TIMESTAMP": 1750120201,
                    "TOTAL_OPEN_INTEREST_UPDATES": 8679521,
                    "CONTRACT_EXPIRATION_TS": null
                }
            }
        }
    },
    "Err": {}
}
```
---