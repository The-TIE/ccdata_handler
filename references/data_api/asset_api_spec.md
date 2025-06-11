# CryptoCompare "Asset API" Specification

This document outlines the key endpoints, parameters, and example responses for the CryptoCompare "Asset API" used in this project.

---
---

## `/asset/v2/metadata`

**Description:**  
The Full Asset Metadata endpoint returns an object that provides detailed and comprehensive information about multiple cryptocurrency assets in response to a request. Each asset can be identified by its CoinDesk asset ID, unique asset symbol, or asset URI, ensuring users receive a broad dataset covering all requested assets. This object consolidates extensive data related to asset description, classification, blockchain properties, social metrics, token sale information, and equity sale details for each asset—facilitating in-depth analysis, development, and research.

**Parameters:**

- `assets` (query, array of strings, required): Specify a list of digital assets for which you want to retrieve information by providing either its unique SYMBOL or the CoinDesk internal asset ID.  
  Example: `["BTC"]`

- `groups` (query, array of strings, optional): Filter by specific groups of interest.  
  Enum: ID, BASIC, SUPPORTED_PLATFORMS, CUSTODIANS, CONTROLLED_ADDRESSES, SECURITY_METRICS, SUPPLY, SUPPLY_ADDRESSES, ASSET_TYPE_SPECIFIC_METRICS, SOCIAL, TOKEN_SALE, EQUITY_SALE, RESOURCE_LINKS, CLASSIFICATION, PRICE, MKT_CAP, VOLUME, CHANGE, TOPLIST_RANK, DESCRIPTION, DESCRIPTION_SUMMARY, CONTACT, SEO, INTERNAL  
  Example: `[]`

- `asset_lookup_priority` (query, string, optional): Specifies the matching priority for the asset key provided in the asset parameter.  
  Enum: SYMBOL, ID, URI  
  Default: SYMBOL  
  Example: `SYMBOL`

- `quote_asset` (query, string, optional): Specify the digital asset for the quote values by providing either the CoinDesk internal asset ID, its unique SYMBOL, or the CoinDesk recommended URI.  
  Default: USD  
  Example: `USD`

- `asset_language` (query, string, optional): Specifies the desired language for localized asset descriptions and other fields that make sense to translate.  
  Enum: en-US, de-DE, es-ES, fr-FR, pt-BR, it-IT, ja-JP, vi-VN, sv-SE, tr-TR, tl-PH, ru-RU, uk-UA, ro-RO  
  Default: en-US  
  Example: `en-US`

**Example Response:**  
```json
{
    "Data": {
        "BTC": {
            "ID": 1,
            "TYPE": "162",
            "ID_LEGACY": 1182,
            "ID_PARENT_ASSET": null,
            "ID_ASSET_ISSUER": null,
            "SYMBOL": "BTC",
            "URI": "bitcoin",
            "ASSET_TYPE": "BLOCKCHAIN",
            "ASSET_ISSUER_NAME": null,
            "PARENT_ASSET_SYMBOL": null,
            "CREATED_ON": 1659708643,
            "UPDATED_ON": 1749179233,
            "PUBLIC_NOTICE": null,
            "NAME": "Bitcoin",
            "LOGO_URL": "https://resources.cryptocompare.com/asset-management/1/1659708726266.png",
            "LAUNCH_DATE": 1230940800,
            "PREVIOUS_ASSET_SYMBOLS": null,
            "ASSET_ALTERNATIVE_IDS": [
                {
                    "NAME": "CMC",
                    "ID": "1"
                },
                {
                    "NAME": "CG",
                    "ID": "bitcoin"
                },
                {
                    "NAME": "ISIN",
                    "ID": "XTV15WLZJMF0"
                },
                {
                    "NAME": "VALOR",
                    "ID": "18789194"
                },
                {
                    "NAME": "DTI",
                    "ID": "V15WLZJMF"
                }
            ],
            "ASSET_DESCRIPTION_SNIPPET": "Bitcoin is a decentralized cryptocurrency that records transactions using blockchain and P2P technology. Verified by miners with a total supply limited to 21 million BTC. Bitcoin is used for transactions, store of value, or investment. ",
            "ASSET_DECIMAL_POINTS": 8,
            "SUPPORTED_PLATFORMS": [
                {
                    "BLOCKCHAIN": "ETH",
                    "BLOCKCHAIN_ASSET_ID": 2,
                    "TOKEN_STANDARD": "ERC20",
                    "EXPLORER_URL": "https://etherscan.io/token/0x2260fac5e5542a773aa44fbcfedf7c193bc2c599",
                    "SMART_CONTRACT_ADDRESS": "0x2260fac5e5542a773aa44fbcfedf7c193bc2c599",
                    "LAUNCH_DATE": 1543276800,
                    "TRADING_AS": "WBTC",
                    "DECIMALS": 8,
                    "IS_INHERITED": true
                },
            ],
            "ASSET_CUSTODIANS": [
                {
                    "NAME": "COINBASE"
                },
            ],
            "CONTROLLED_ADDRESSES": null,
            "ASSET_SECURITY_METRICS": [
                {
                    "NAME": "CERTIK",
                    "OVERALL_SCORE": 97.53,
                    "OVERALL_RANK": 1,
                    "UPDATED_AT": 1749081600
                }
            ],
            "SUPPLY_MAX": 20999999.9769,
            "SUPPLY_ISSUED": 19874925,
            "SUPPLY_TOTAL": 19874925,
            "SUPPLY_CIRCULATING": 19874925,
            "SUPPLY_FUTURE": 1125074.9769,
            "SUPPLY_LOCKED": 0,
            "SUPPLY_BURNT": 0,
            "SUPPLY_STAKED": 0,
            "LAST_BLOCK_MINT": 3.125,
            "LAST_BLOCK_BURN": null,
            "BURN_ADDRESSES": null,
            "LOCKED_ADDRESSES": null,
            "HAS_SMART_CONTRACT_CAPABILITIES": true,
            "SMART_CONTRACT_SUPPORT_TYPE": "BASIC_LOGIC_AND_SCRIPTING",
            "TARGET_BLOCK_MINT": 3.125,
            "TARGET_BLOCK_TIME": 600,
            "LAST_BLOCK_NUMBER": 899982,
            "LAST_BLOCK_TIMESTAMP": 1749178005,
            "LAST_BLOCK_TIME": 436,
            "LAST_BLOCK_SIZE": 2415683,
            "LAST_BLOCK_ISSUER": null,
            "LAST_BLOCK_TRANSACTION_FEE_TOTAL": null,
            "LAST_BLOCK_TRANSACTION_COUNT": 1312,
            "LAST_BLOCK_HASHES_PER_SECOND": 833921654247199700000,
            "LAST_BLOCK_DIFFICULTY": 126982285146989.3,
            "SUPPORTED_STANDARDS": [
                {
                    "NAME": "BRC20"
                },
                "LAYER_TWO_SOLUTIONS": [
                    {
                        "NAME": "Lightning Network",
                        "WEBSITE_URL": "https://lightning.network/",
                        "DESCRIPTION": "The Lightning Network is dependent upon the underlying technology of the blockchain. By using real Bitcoin/blockchain transactions and using its native smart-contract scripting language, it is possible to create a secure network of participants which are able to transact at high volume and high speed.",
                        "CATEGORY": "STATE_CHANNEL"
                    },
                ],
                "PRIVACY_SOLUTIONS": [
                    {
                        "NAME": "Yo!Mix",
                        "WEBSITE_URL": "https://yomix.io/",
                        "DESCRIPTION": "Yo!Mix Bitcoin Mixer is a sophisticated service that enhances the privacy of Bitcoin transactions. It functions by mixing the coins involved in transactions, which makes it extremely challenging to trace the origins of the funds. This service stands out as a more advanced alternative to traditional Bitcoin mixers by providing enhanced security features and robust privacy measures.",
                        "PRIVACY_SOLUTION_TYPE": "EXTERNAL"
                    },
                ],
                "CODE_REPOSITORIES": [
                    {
                        "URL": "https://github.com/bitcoin/bitcoin",
                        "MAKE_3RD_PARTY_REQUEST": true,
                        "OPEN_ISSUES": 743,
                        "CLOSED_ISSUES": 0,
                        "OPEN_PULL_REQUESTS": 331,
                        "CLOSED_PULL_REQUESTS": 22169,
                        "CONTRIBUTORS": 1247,
                        "FORKS": 37312,
                        "STARS": 83986,
                        "SUBSCRIBERS": 4037,
                        "LAST_UPDATED_TS": 1749179233,
                        "CREATED_AT": 1292771803,
                        "UPDATED_AT": 1749171749,
                        "LAST_PUSH_TS": 1749130584,
                        "CODE_SIZE_IN_BYTES": 283337,
                        "IS_FORK": false,
                        "LANGUAGE": "C++",
                        "FORKED_ASSET_DATA": null
                    }
                ],
                "SUBREDDITS": [
                    {
                        "URL": "https://www.reddit.com/r/Bitcoin",
                        "MAKE_3RD_PARTY_REQUEST": true,
                        "NAME": "Bitcoin",
                        "CURRENT_ACTIVE_USERS": 1791,
                        "AVERAGE_POSTS_PER_DAY": 76.32,
                        "AVERAGE_POSTS_PER_HOUR": 3.18,
                        "AVERAGE_COMMENTS_PER_DAY": 2264.15,
                        "AVERAGE_COMMENTS_PER_HOUR": 94.34,
                        "SUBSCRIBERS": 7550803,
                        "COMMUNITY_CREATED_AT": 1284042626,
                        "LAST_UPDATED_TS": 1736510655
                    }
                ],
                "TWITTER_ACCOUNTS": [
                    {
                        "URL": "https://twitter.com/Bitcoin",
                        "MAKE_3RD_PARTY_REQUEST": true,
                        "NAME": "Bitcoin",
                        "USERNAME": "Bitcoin",
                        "VERIFIED": true,
                        "VERIFIED_TYPE": "blue",
                        "FOLLOWING": 0,
                        "FOLLOWERS": 7757552,
                        "FAVOURITES": 0,
                        "LISTS": 22178,
                        "STATUSES": 28442,
                        "ACCOUNT_CREATED_AT": 1313643968,
                        "LAST_UPDATED_TS": 1749179116
                    }
                ],
                "DISCORD_SERVERS": null,
                "TELEGRAM_GROUPS": null,
                "OTHER_SOCIAL_NETWORKS": [
                    {
                        "NAME": "BITCOINTALK",
                        "URL": "https://bitcointalk.org/index.php"
                    }
                ],
                "HELD_TOKEN_SALE": false,
                "HELD_EQUITY_SALE": false,
                "WEBSITE_URL": "https://bitcoin.org",
                "BLOG_URL": "https://bitcoin.org/en/blog",
                "WHITE_PAPER_URL": "https://resources.cryptocompare.com/asset-management/1/1659709016925.pdf",
                "OTHER_DOCUMENT_URLS": null,
                "EXPLORER_ADDRESSES": [
                    {
                        "URL": "https://blockchain.info/"
                    },
                ],
                "RPC_OPERATORS": null,
                "ASSET_SYMBOL_GLYPH": "₿",
                "IS_EXCLUDED_FROM_PRICE_TOPLIST": null,
                "IS_EXCLUDED_FROM_VOLUME_TOPLIST": null,
                "IS_EXCLUDED_FROM_MKT_CAP_TOPLIST": null,
                "ASSET_INDUSTRIES": [
                    {
                        "ASSET_INDUSTRY": "PAYMENT",
                        "JUSTIFICATION": "Bitcoin is primarily designed.."
                    }
                ],
                "CONSENSUS_MECHANISMS": [
                    {
                        "NAME": "POW"
                    }
                ],
                "CONSENSUS_ALGORITHM_TYPES": [
                    {
                        "NAME": "Nakamoto Consensus",
                        "DESCRIPTION": "The Nakamoto Consensus algorithm..."
                    }
                ],
                "HASHING_ALGORITHM_TYPES": [
                    {
                        "NAME": "SHA_256"
                    }
                ],
                "PRICE_USD": 102180.903914994,
                "PRICE_USD_SOURCE": "cadli",
                "PRICE_USD_LAST_UPDATE_TS": 1749179118,
                "PRICE_CONVERSION_ASSET": {
                    "ID": 5,
                    "SYMBOL": "USD",
                    "ASSET_TYPE": "FIAT"
                },
                "PRICE_CONVERSION_RATE": 1,
                "PRICE_CONVERSION_VALUE": 102180.903914994,
                "PRICE_CONVERSION_SOURCE": "cadli",
                "PRICE_CONVERSION_LAST_UPDATE_TS": 1749179317,
                "MKT_CAP_PENALTY": 0,
                "CIRCULATING_MKT_CAP_USD": 2030837801742.7122,
                "TOTAL_MKT_CAP_USD": 2030837801742.7122,
                "CIRCULATING_MKT_CAP_CONVERSION": 2030837801742.71,
                "TOTAL_MKT_CAP_CONVERSION": 2030837801742.71,
                "SPOT_MOVING_24_HOUR_QUOTE_VOLUME_TOP_TIER_DIRECT_USD": 3095135630.12989,
                "SPOT_MOVING_24_HOUR_QUOTE_VOLUME_DIRECT_USD": 3608357065.32126,
                "SPOT_MOVING_24_HOUR_QUOTE_VOLUME_TOP_TIER_USD": 15611740418.7024,
                "SPOT_MOVING_24_HOUR_QUOTE_VOLUME_USD": 26388134034.3908,
                "SPOT_MOVING_24_HOUR_QUOTE_VOLUME_TOP_TIER_CONVERSION": 15611740418.7024,
                "SPOT_MOVING_24_HOUR_QUOTE_VOLUME_CONVERSION": 26388134034.3908,
                "SPOT_MOVING_7_DAY_QUOTE_VOLUME_TOP_TIER_DIRECT_USD": 9721147118.46679,
                "SPOT_MOVING_7_DAY_QUOTE_VOLUME_DIRECT_USD": 11793977361.7591,
                "SPOT_MOVING_7_DAY_QUOTE_VOLUME_TOP_TIER_USD": 55548742235.8768,
                "SPOT_MOVING_7_DAY_QUOTE_VOLUME_USD": 102645549206.988,
                "SPOT_MOVING_7_DAY_QUOTE_VOLUME_TOP_TIER_CONVERSION": 55548742235.8768,
                "SPOT_MOVING_7_DAY_QUOTE_VOLUME_CONVERSION": 102645549206.988,
                "SPOT_MOVING_30_DAY_QUOTE_VOLUME_TOP_TIER_DIRECT_USD": 59055663421.8954,
                "SPOT_MOVING_30_DAY_QUOTE_VOLUME_DIRECT_USD": 73588191597.4608,
                "SPOT_MOVING_30_DAY_QUOTE_VOLUME_TOP_TIER_USD": 332601216875.453,
                "SPOT_MOVING_30_DAY_QUOTE_VOLUME_USD": 630759049057.74,
                "SPOT_MOVING_30_DAY_QUOTE_VOLUME_TOP_TIER_CONVERSION": 332601216875.453,
                "SPOT_MOVING_30_DAY_QUOTE_VOLUME_CONVERSION": 630759049057.74,
                "SPOT_MOVING_24_HOUR_CHANGE_USD": -2889.095809543,
                "SPOT_MOVING_24_HOUR_CHANGE_PERCENTAGE_USD": -2.74968670135849,
                "SPOT_MOVING_24_HOUR_CHANGE_CONVERSION": -2889.095809543,
                "SPOT_MOVING_24_HOUR_CHANGE_PERCENTAGE_CONVERSION": -2.74968670135849,
                "SPOT_MOVING_7_DAY_CHANGE_USD": -1860.640982191,
                "SPOT_MOVING_7_DAY_CHANGE_PERCENTAGE_USD": -1.7883634696406199,
                "SPOT_MOVING_7_DAY_CHANGE_CONVERSION": -1860.640982191,
                "SPOT_MOVING_7_DAY_CHANGE_PERCENTAGE_CONVERSION": -1.7883634696406199,
                "SPOT_MOVING_30_DAY_CHANGE_USD": 5107.52840331991,
                "SPOT_MOVING_30_DAY_CHANGE_PERCENTAGE_USD": 5.26151313519089,
                "SPOT_MOVING_30_DAY_CHANGE_CONVERSION": 5107.52840331991,
                "SPOT_MOVING_30_DAY_CHANGE_PERCENTAGE_CONVERSION": 5.26151313519089,
                "TOPLIST_BASE_RANK": {
                    "CREATED_ON": 1,
                    "LAUNCH_DATE": 1,
                    "CIRCULATING_MKT_CAP_USD": 1,
                    "TOTAL_MKT_CAP_USD": 2,
                    "SPOT_MOVING_24_HOUR_QUOTE_VOLUME_USD": 1,
                    "SPOT_MOVING_7_DAY_QUOTE_VOLUME_USD": 1,
                    "SPOT_MOVING_30_DAY_QUOTE_VOLUME_USD": 1
                },
                "ASSET_DESCRIPTION": "## What is Bitcoin?...",
                "ASSET_DESCRIPTION_SUMMARY": "Bitcoin...",
                "PROJECT_LEADERS": [
                    {
                        "LEADER_TYPE": "FOUNDER",
                        "FULL_NAME": "Satoshi Nakamoto"
                    }
                ],
                "ASSOCIATED_CONTACT_DETAILS": [
                    {
                        "CONTACT_MEDIUM": "EMAIL_ADDRESS",
                        "FULL_NAME": "Satoshi Nakamoto"
                    },
                ],
                "SEO_TITLE": "Bitcoin (BTC)",
                "SEO_DESCRIPTION": "Live Bitcoin price movements from all markets and BTC market cap, use our charts and see when there is an opportunity to buy or sell."
            }
        },
        "Warn": {},
        "Err": {}
    }
```
---

## `/asset/v1/top/list` and Variants

**Description:**  
These endpoints provide ranked overviews of digital assets and industries based on critical financial metrics like market capitalization, trading volume, and price changes. They support filtering by consensus mechanism, hashing algorithm type, or smart contract support type, and use pagination to efficiently navigate extensive data. The response structure is identical for all variants.

**Endpoints:**
- `/asset/v1/top/list`
- `/asset/v1/top/list/consensus-mechanism` (adds `consensus_mechanism` parameter)
- `/asset/v1/top/list/hashing-algorithm-type` (adds `hashing_algorithm_type` parameter)
- `/asset/v1/top/list/smart-contract-support-type` (adds `smart_contract_support_type` parameter)

**Parameters:**

- `page` (query, integer, optional): The page number for the request to get {page_size} coins at the time.  
  Default: 1, Min: 1, Max: 1000  
  Example: `1`

- `page_size` (query, integer, optional): The number of items returned per page.  
  Default: 100, Min: 10, Max: 100  
  Example: `10`

- `sort_by` (query, string, optional): Sort by field.  
  Default: CIRCULATING_MKT_CAP_USD  
  Example: `CIRCULATING_MKT_CAP_USD`

- `sort_direction` (query, string, optional): Sort direction.  
  Enum: DESC, ASC  
  Default: DESC  
  Example: `DESC`

- `groups` (query, array of strings, optional): Filter by specific groups of interest.  
  Example: `["ID", "BASIC", "SUPPLY", "PRICE", "MKT_CAP", "VOLUME", "CHANGE", "TOPLIST_RANK"]`

- `toplist_quote_asset` (query, string, optional): Specify the digital asset for the quote values.  
  Default: USD  
  Example: `USD`

- `asset_type` (query, string, optional): Filter the returned assets based on their type.  
  Enum: BLOCKCHAIN, FIAT, TOKEN, STOCK, INDEX, COMMODITY, ETF  
  Example: `BLOCKCHAIN`

- `asset_industry` (query, string, optional): Filter the returned assets based on their industry.  
  Example: `PAYMENT`

- `consensus_mechanism` (query, string, required for `/consensus-mechanism`): Filter by consensus mechanism.  
  Example: `POW`

- `hashing_algorithm_type` (query, string, required for `/hashing-algorithm-type`): Filter by hashing algorithm type.  
  Example: `SHA_256`

- `smart_contract_support_type` (query, string, required for `/smart-contract-support-type`): Filter by smart contract support type.  
  Example: `ADVANCED_EXECUTION_RIGHTS`

**Example Response:**  
```json
{
    "Data": {
        "STATS": {
            "PAGE": 1,
            "PAGE_SIZE": 10,
            "TOTAL_ASSETS": 3396
        },
        "LIST": [
            {
                "ID": 1,
                "TYPE": "162",
                "ID_LEGACY": 1182,
                "ID_PARENT_ASSET": null,
                "ID_ASSET_ISSUER": null,
                "SYMBOL": "BTC",
                "URI": "bitcoin",
                "ASSET_TYPE": "BLOCKCHAIN",
                "ASSET_ISSUER_NAME": null,
                "PARENT_ASSET_SYMBOL": null,
                "CREATED_ON": 1659708643,
                "UPDATED_ON": 1749179233,
                "PUBLIC_NOTICE": null,
                "NAME": "Bitcoin",
                "LOGO_URL": "https://resources.cryptocompare.com/asset-management/1/1659708726266.png",
                "LAUNCH_DATE": 1230940800,
                "PREVIOUS_ASSET_SYMBOLS": null,
                "ASSET_ALTERNATIVE_IDS": [
                    {
                        "NAME": "CMC",
                        "ID": "1"
                    },
                    {
                        "NAME": "CG",
                        "ID": "bitcoin"
                    },
                    {
                        "NAME": "ISIN",
                        "ID": "XTV15WLZJMF0"
                    },
                    {
                        "NAME": "VALOR",
                        "ID": "18789194"
                    },
                    {
                        "NAME": "DTI",
                        "ID": "V15WLZJMF"
                    }
                ],
                "ASSET_DESCRIPTION_SNIPPET": "Bitcoin is a decentralized cryptocurrency that records transactions using blockchain and P2P technology. Verified by miners with a total supply limited to 21 million BTC. Bitcoin is used for transactions, store of value, or investment. ",
                "ASSET_DECIMAL_POINTS": 8,
                "SUPPLY_MAX": 20999999.9769,
                "SUPPLY_ISSUED": 19874925,
                "SUPPLY_TOTAL": 19874925,
                "SUPPLY_CIRCULATING": 19874925,
                "SUPPLY_FUTURE": 1125074.9769,
                "SUPPLY_LOCKED": 0,
                "SUPPLY_BURNT": 0,
                "SUPPLY_STAKED": 0,
                "LAST_BLOCK_MINT": 3.125,
                "LAST_BLOCK_BURN": null,
                "PRICE_USD": 102564.643975363,
                "PRICE_USD_SOURCE": "cadli",
                "PRICE_USD_LAST_UPDATE_TS": 1749180973,
                "PRICE_CONVERSION_ASSET": {
                    "ID": 5,
                    "SYMBOL": "USD",
                    "ASSET_TYPE": "FIAT"
                },
                "PRICE_CONVERSION_RATE": 1,
                "PRICE_CONVERSION_VALUE": 102564.643975363,
                "PRICE_CONVERSION_SOURCE": "cadli",
                "PRICE_CONVERSION_LAST_UPDATE_TS": 1749181065,
                "MKT_CAP_PENALTY": 0,
                "CIRCULATING_MKT_CAP_USD": 2038464606662.0415,
                "TOTAL_MKT_CAP_USD": 2038464606662.0415,
                "CIRCULATING_MKT_CAP_CONVERSION": 2038464606662.04,
                "TOTAL_MKT_CAP_CONVERSION": 2038464606662.04,
                "SPOT_MOVING_24_HOUR_QUOTE_VOLUME_TOP_TIER_DIRECT_USD": 3144698798.21469,
                "SPOT_MOVING_24_HOUR_QUOTE_VOLUME_DIRECT_USD": 3669682069.47431,
                "SPOT_MOVING_24_HOUR_QUOTE_VOLUME_TOP_TIER_USD": 15878783333.8503,
                "SPOT_MOVING_24_HOUR_QUOTE_VOLUME_USD": 26913933943.9413,
                "SPOT_MOVING_24_HOUR_QUOTE_VOLUME_TOP_TIER_CONVERSION": 15878783333.8503,
                "SPOT_MOVING_24_HOUR_QUOTE_VOLUME_CONVERSION": 26913933943.9413,
                "SPOT_MOVING_7_DAY_QUOTE_VOLUME_TOP_TIER_DIRECT_USD": 9770710286.55161,
                "SPOT_MOVING_7_DAY_QUOTE_VOLUME_DIRECT_USD": 11855302365.9122,
                "SPOT_MOVING_7_DAY_QUOTE_VOLUME_TOP_TIER_USD": 55815785151.0247,
                "SPOT_MOVING_7_DAY_QUOTE_VOLUME_USD": 103171349116.539,
                "SPOT_MOVING_7_DAY_QUOTE_VOLUME_TOP_TIER_CONVERSION": 55815785151.0247,
                "SPOT_MOVING_7_DAY_QUOTE_VOLUME_CONVERSION": 103171349116.539,
                "SPOT_MOVING_30_DAY_QUOTE_VOLUME_TOP_TIER_DIRECT_USD": 59105226589.9802,
                "SPOT_MOVING_30_DAY_QUOTE_VOLUME_DIRECT_USD": 73649516601.6138,
                "SPOT_MOVING_30_DAY_QUOTE_VOLUME_TOP_TIER_USD": 332868259790.6,
                "SPOT_MOVING_30_DAY_QUOTE_VOLUME_USD": 631284848967.291,
                "SPOT_MOVING_30_DAY_QUOTE_VOLUME_TOP_TIER_CONVERSION": 332868259790.6,
                "SPOT_MOVING_30_DAY_QUOTE_VOLUME_CONVERSION": 631284848967.291,
                "SPOT_MOVING_24_HOUR_CHANGE_USD": -2505.355749174,
                "SPOT_MOVING_24_HOUR_CHANGE_PERCENTAGE_USD": -2.38446345840136,
                "SPOT_MOVING_24_HOUR_CHANGE_CONVERSION": -2505.355749174,
                "SPOT_MOVING_24_HOUR_CHANGE_PERCENTAGE_CONVERSION": -2.38446345840136,
                "SPOT_MOVING_7_DAY_CHANGE_USD": -1476.900921822,
                "SPOT_MOVING_7_DAY_CHANGE_PERCENTAGE_USD": -1.41952998033765,
                "SPOT_MOVING_7_DAY_CHANGE_CONVERSION": -1476.900921822,
                "SPOT_MOVING_7_DAY_CHANGE_PERCENTAGE_CONVERSION": -1.41952998033765,
                "SPOT_MOVING_30_DAY_CHANGE_USD": 5491.2684636889,
                "SPOT_MOVING_30_DAY_CHANGE_PERCENTAGE_USD": 5.65682241370963,
                "SPOT_MOVING_30_DAY_CHANGE_CONVERSION": 5491.2684636889,
                "SPOT_MOVING_30_DAY_CHANGE_PERCENTAGE_CONVERSION": 5.65682241370963,
                "TOPLIST_BASE_RANK": {
                    "CREATED_ON": 1,
                    "LAUNCH_DATE": 1,
                    "CIRCULATING_MKT_CAP_USD": 1,
                    "TOTAL_MKT_CAP_USD": 2,
                    "SPOT_MOVING_24_HOUR_QUOTE_VOLUME_USD": 1,
                    "SPOT_MOVING_7_DAY_QUOTE_VOLUME_USD": 1,
                    "SPOT_MOVING_30_DAY_QUOTE_VOLUME_USD": 1
                }
            },
        ]
    },
    "Err": {}
}
```
---

## `/asset/v1/search`

**Description:**  
The Asset Search endpoint provides comprehensive search functionality within the asset database, allowing users to retrieve assets based on symbols, names, or IDs. It supports both textual and numerical queries, intelligently prioritizing exact matches and relevance to deliver precise search results, enhancing user exploration and asset discovery.

**Parameters:**

- `search_string` (query, string, optional): Search assets by symbols, names, or IDs.  
  Example: `BTC`

- `limit` (query, integer, optional): The number of search results to return.  
  Default: 20, Min: 1, Max: 100  
  Example: `20`

**Example Response:**  
```json
{
    "Data": {
        "LIST": [
            {
                "TYPE": "147",
                "ID": 18268,
                "SYMBOL": "SCA",
                "URI": "sca",
                "IS_PUBLIC": true,
                "NAME": "Scallop",
                "LOGO_URL": "https://resources.cryptocompare.com/asset-management/18268/1735908335181.png",
                "ASSET_TYPE": "TOKEN",
                "HAS_SMART_CONTRACT_CAPABILITIES": false,
                "CIRCULATING_MKT_CAP_USD": 10861833.570590308,
                "ID_PARENT_ASSET": null,
                "PARENT_ASSET_SYMBOL": null,
                "ROOT_ASSET_ID": null,
                "ROOT_ASSET_SYMBOL": null,
                "ROOT_ASSET_TYPE": null,
                "CREATED_ON": 1735908325
            },
        ]
    },
    "Err": {}
}
```
---

## `/asset/v1/summary/list`

**Description:**  
The Asset Summary List endpoint efficiently retrieves a summarized list of all digital assets, grouped by their respective asset types. It provides essential information for each asset, including the ID, SYMBOL, ASSET_TYPE, NAME, and LOGO_URL. Designed for straightforward and fast access to basic asset details, this endpoint is particularly useful for applications requiring a quick overview of a large number of assets without delving into more complex data.

**Parameters:**

- `asset_type` (query, string, optional): Filter the returned assets based on their type.  
  Enum: BLOCKCHAIN, FIAT, TOKEN, STOCK, INDEX, COMMODITY, ETF  
  Example: `BLOCKCHAIN`

- `filters` (query, array of strings, optional): Filter assets by specific features.  
  Enum: HAS_CODE_REPOSITORIES, HAS_SUBREDDITS, HAS_TWITTER_ACCOUNTS, HAS_DISCORD_SERVERS, HAS_TELEGRAM_GROUPS, HAS_SUPPORTED_PLATFORMS, IS_SUPPORTING_OTHER_ASSETS  
  Example: `[]`

- `assets` (query, array of strings, optional): Specify a list of digital assets for which you want to retrieve information by providing either its unique SYMBOL or the CoinDesk internal asset ID.  
  Example: `["BTC", "ETH"]`

- `asset_lookup_priority` (query, string, optional): Specifies the matching priority for the asset key provided in the asset parameter.  
  Enum: SYMBOL, ID  
  Default: SYMBOL  
  Example: `SYMBOL`

**Example Response:**  
```json
{
    "Data": {
        "STATS": {
            "TOTAL_ASSETS": 18897,
            "TOTAL_FILTERED_ASSETS": 18897
        },
        "LIST": [
            {
                "TYPE": "168",
                "ID": 19347,
                "SYMBOL": "1",
                "ASSET_TYPE": "TOKEN",
                "NAME": "just buy $1 worth of this coin",
                "LOGO_URL": "https://resources.cryptocompare.com/asset-management/19347/1745333956329.png",
                "LAUNCH_DATE": 1732406400
            },
        ]
    },
    "Err": {}
}
```
---

## `/asset/v1/events`

**Description:**  
The Asset Events endpoint retrieves an array of significant events related to digital assets, such as security incidents, rebrandings, blockchain forks, and other impactful developments. Events are returned in chronological order, with the most recent events appearing first.

**Parameters:**

- `asset` (query, string, required): Specify the digital asset for which you want to retrieve information by providing either its unique SYMBOL or the CoinDesk internal asset ID.  
  Example: `BTC`

- `limit` (query, integer, optional): The number of events to return.  
  Default: 30, Min: 1, Max: 100  
  Example: `30`

- `to_ts` (query, integer, optional): Returns events before this unix timestamp.  
  Example: `1622505600`

- `asset_lookup_priority` (query, string, optional): Specifies the matching priority for the asset key provided in the asset parameter.  
  Enum: SYMBOL, ID  
  Default: SYMBOL  
  Example: `SYMBOL`

**Example Response:**  
```json
{
    "Data": [
        {
            "TYPE": "146",
            "ID": 515,
            "ASSET_ID": 1,
            "EVENT_TYPE": "OTHER",
            "ANNOUNCED_ON": 1717200000,
            "IMPLEMENTATION_START_DATE": 1717200000,
            "IMPLEMENTATION_END_DATE": 1720742400,
            "NAME": "Germany's Bitcoin Reserves Liquidation",
            "DESCRIPTION": "In June 2024, the German government began selling approximately 50,000 BTC seized in a criminal case. The liquidation, which concluded on 12th July 2024, involved large transfers to major exchanges and led to a temporary decline in Bitcoin’s price. This action, aimed at realigning financial strategies, drew criticism but was seen as necessary by the government​.",
            "METADATA": {},
            "CREATED_ON": 1723451673,
            "UPDATED_ON": null
        },
    ],
    "Err": {}
}
```