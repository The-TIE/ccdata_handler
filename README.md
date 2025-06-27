# CryptoCompare Data Handler

A comprehensive, production-ready data ingestion and management system for CryptoCompare cryptocurrency data with advanced monitoring, caching, and error handling capabilities.

## 🌟 Key Features

- **🚀 Unified Ingestion Framework** - Single entry point for all data types (spot, futures, indices, metadata)
- **⚡ Asynchronous Processing** - High-performance async operations using `asyncio` and `aiohttp`
- **📊 Advanced Monitoring** - Real-time performance tracking, health checks, and alerting
- **🔄 Intelligent Caching** - Multi-backend caching system for improved performance
- **🛡️ Robust Error Handling** - Comprehensive retry mechanisms and graceful failure recovery
- **🏗️ Modular Architecture** - Clean separation of concerns with pluggable components
- **📈 Production Ready** - Battle-tested with comprehensive logging, monitoring, and configuration management

## 🚀 Quick Start with Unified Ingestion

The new **Unified Ingestion Framework** provides a single, powerful interface for all your data ingestion needs, replacing the need for multiple separate scripts.

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd ccdata_handler

# Install dependencies
pip install -e .

# Set up environment variables
cp .env.example .env
# Edit .env with your configuration
```

### Basic Usage

```bash
# Ingest spot market data for top 50 trading pairs
python scripts/unified_ingest.py spot_ohlcv --pair_limit 50 --interval 1d

# Ingest futures data with monitoring enabled
python scripts/unified_ingest.py futures_ohlcv --enable_monitoring --interval 1h

# Ingest cryptocurrency metadata
python scripts/unified_ingest.py asset_metadata

# Run batch operations from configuration file
python scripts/unified_ingest.py batch --config batch_config.json --enable_monitoring

# Check system status and health
python scripts/unified_ingest.py status --enable_monitoring
```

### Advanced Features

```bash
# High-performance ingestion with caching and parallel processing
python scripts/unified_ingest.py spot_ohlcv \
  --pair_limit 200 \
  --interval 1d \
  --enable_monitoring \
  --enable_caching \
  --parallel_workers 8

# Futures data ingestion for specific exchanges
python scripts/unified_ingest.py futures_ohlcv \
  --interval 1h \
  --exchanges binance okex bybit \
  --enable_monitoring

# Indices data for top assets
python scripts/unified_ingest.py indices_ohlcv \
  --asset_limit 100 \
  --market cadli \
  --interval 1d
```

## 🏗️ Architecture Overview

The system is built around a modern, asynchronous architecture designed for scalability and maintainability:

```
┌─────────────────────────────────────────────────────────────┐
│                    Unified Ingestion CLI                    │
│                  (scripts/unified_ingest.py)               │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────┐
│                 Ingestion Framework                         │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────────────────┐│
│  │   Config    │ │ Monitoring  │ │       Caching           ││
│  │ Management  │ │ & Alerting  │ │      System             ││
│  └─────────────┘ └─────────────┘ └─────────────────────────┘│
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────┐
│                Specialized Ingestors                        │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────────────────┐│
│  │    Spot     │ │   Futures   │ │      Metadata           ││
│  │   OHLCV     │ │    Data     │ │     Ingestors           ││
│  └─────────────┘ └─────────────┘ └─────────────────────────┘│
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────┐
│                  API Client Layer                           │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────────────────┐│
│  │    Spot     │ │   Futures   │ │       Asset             ││
│  │ API Client  │ │ API Client  │ │    API Client           ││
│  └─────────────┘ └─────────────┘ └─────────────────────────┘│
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────┐
│                 Database Layer                              │
│              (SingleStore Database)                         │
└─────────────────────────────────────────────────────────────┘
```

## 📊 Supported Data Types

| Data Type | Description | Intervals | CLI Command |
|-----------|-------------|-----------|-------------|
| **Spot OHLCV** | Spot market price data | 1d, 1h, 1m | `spot_ohlcv` |
| **Futures OHLCV** | Futures contract price data | 1d, 1h, 1m | `futures_ohlcv` |
| **Futures Funding** | Funding rate data | 1d, 1h, 1m | `futures_funding_rate` |
| **Futures OI** | Open interest data | 1d, 1h, 1m | `futures_open_interest` |
| **Indices OHLCV** | Index price data | 1d, 1h, 1m | `indices_ohlcv` |
| **Asset Metadata** | Cryptocurrency information | N/A | `asset_metadata` |
| **Exchange Metadata** | Exchange information | N/A | `exchange_metadata` |
| **Instruments** | Trading pair/instrument data | N/A | `spot_instruments`, `futures_instruments` |

## 🔧 Configuration

### Environment Variables

```bash
# Database Configuration
S2_HOST=your-singlestore-host
S2_PORT=3306
S2_USER=your-username
S2_PASSWORD=your-password
S2_DATABASE=your-database

# API Configuration
CCDATA_API_KEY=your-cryptocompare-api-key
DATA_API_BASE_URL=https://data-api.cryptocompare.com
MIN_API_BASE_URL=https://min-api.cryptocompare.com/data

# Performance Tuning
INGESTION_BATCH_SIZE=1000
INGESTION_PARALLEL_WORKERS=4
API_RATE_LIMIT_PER_SECOND=10.0
API_RATE_LIMIT_PER_MINUTE=300

# Monitoring & Logging
LOG_LEVEL=INFO
MONITORING_METRICS_ENABLED=true
MONITORING_PERFORMANCE_ENABLED=true
```

### Batch Configuration Example

```json
[
  {
    "data_type": "spot_ohlcv",
    "interval": "1d",
    "pair_limit": 100
  },
  {
    "data_type": "futures_ohlcv",
    "interval": "1d",
    "exchanges": ["binance", "okex"]
  },
  {
    "data_type": "asset_metadata"
  },
  {
    "data_type": "indices_ohlcv",
    "interval": "1d",
    "asset_limit": 50,
    "market": "cadli"
  }
]
```

## 🆚 Unified Framework vs Legacy Scripts

### ✅ Unified Framework Benefits

- **Single Entry Point**: One CLI tool for all ingestion operations
- **Consistent Interface**: Standardized parameters and behavior across all data types
- **Advanced Monitoring**: Built-in performance tracking, health checks, and alerting
- **Intelligent Caching**: Automatic caching of frequently accessed data
- **Robust Error Handling**: Comprehensive retry logic and graceful failure recovery
- **Parallel Processing**: Efficient concurrent operations for improved throughput
- **Configuration Management**: Centralized, environment-aware configuration
- **Production Ready**: Comprehensive logging, monitoring, and operational features

### ❌ Legacy Script Limitations

- **Code Duplication**: Repetitive setup and configuration code across scripts
- **Inconsistent Patterns**: Different approaches for similar operations
- **Limited Error Handling**: Basic retry logic and error recovery
- **No Monitoring**: Minimal visibility into performance and health
- **Manual Coordination**: Difficult to orchestrate multiple ingestion operations
- **Maintenance Overhead**: Multiple scripts to maintain and update

### Migration Path

The unified framework is designed to be a drop-in replacement for legacy scripts:

```bash
# Legacy approach (multiple scripts)
python scripts/ingest_daily_ohlcv_spot_data.py
python scripts/ingest_futures_data.py
python scripts/ingest_asset_data.py

# Unified approach (single script, batch operation)
python scripts/unified_ingest.py batch --config daily_batch.json --enable_monitoring
```

## 📈 Performance & Monitoring

### Real-time Monitoring

```bash
# Enable comprehensive monitoring
python scripts/unified_ingest.py spot_ohlcv \
  --enable_monitoring \
  --pair_limit 100

# Check system health and performance
python scripts/unified_ingest.py status --enable_monitoring
```

### Performance Optimization

```bash
# High-throughput configuration
python scripts/unified_ingest.py futures_ohlcv \
  --parallel_workers 8 \
  --enable_caching \
  --exchanges binance okex bybit
```

### Monitoring Features

- **Performance Tracking**: Automatic measurement of ingestion rates, latency, and success rates
- **Health Monitoring**: Continuous system health checks with configurable intervals
- **Alerting System**: Automatic alerts on failures, performance degradation, and system issues
- **Resource Monitoring**: Track CPU, memory, and I/O usage during ingestion operations
- **Data Quality Metrics**: Monitor data freshness, completeness, and integrity

## 🛠️ Development & Testing

### Project Structure

```
ccdata_handler/
├── src/
│   ├── ingestion/           # Unified ingestion framework
│   │   ├── config.py        # Configuration management
│   │   ├── base.py          # Base ingestor class
│   │   ├── cache.py         # Caching system
│   │   ├── monitoring.py    # Monitoring and alerting
│   │   └── ingestors/       # Specialized ingestors
│   ├── data_api/            # API client implementations
│   ├── db/                  # Database abstraction layer
│   └── utils/               # Shared utilities
├── scripts/
│   ├── unified_ingest.py    # Main CLI entry point
│   └── legacy/              # Legacy scripts (deprecated)
├── tests/                   # Comprehensive test suite
├── docs/                    # Documentation
└── sql/                     # Database schema and migrations
```

### Running Tests

```bash
# Run all tests
python -m pytest tests/

# Run with coverage
python -m pytest tests/ --cov=src --cov-report=html

# Run specific test categories
python -m pytest tests/ingestion/  # Ingestion framework tests
python -m pytest tests/api/        # API client tests
```

### Development Setup

```bash
# Install development dependencies
pip install -e ".[dev]"

# Set up pre-commit hooks
pre-commit install

# Run code quality checks
black src/ tests/
flake8 src/ tests/
mypy src/
```

## 🔄 Scheduling & Automation

### Cron Examples

```bash
# Daily spot data ingestion
0 2 * * * cd /path/to/ccdata_handler && python scripts/unified_ingest.py spot_ohlcv --interval 1d --pair_limit 100

# Hourly futures data
0 * * * * cd /path/to/ccdata_handler && python scripts/unified_ingest.py futures_ohlcv --interval 1h --enable_monitoring

# Weekly metadata refresh
0 3 * * 0 cd /path/to/ccdata_handler && python scripts/unified_ingest.py batch --config weekly_metadata.json
```

### Docker Support

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY . .
RUN pip install -e .

# Run unified ingestion
CMD ["python", "scripts/unified_ingest.py", "batch", "--config", "production_batch.json", "--enable_monitoring"]
```

## 📚 Documentation

- **[📖 Unified Ingestion Guide](README_UNIFIED_INGESTION.md)** - Comprehensive guide to the unified ingestion framework
- **[🏗️ Technical Guidelines](docs/data_ingestion_technical_guidelines.md)** - Detailed technical documentation and architecture
- **[🗄️ Database Schema](database_schema.md)** - Database structure and relationships
- **[🔌 API References](references/data_api/)** - CryptoCompare API documentation and specifications

## 🤝 Contributing

1. **Follow Standards**: Adhere to the coding standards outlined in the technical guidelines
2. **Write Tests**: Include comprehensive tests for new features and bug fixes
3. **Update Documentation**: Keep documentation current with any API or functionality changes
4. **Use Unified Patterns**: Leverage the unified ingestion framework patterns for consistency

### Development Workflow

```bash
# Create feature branch
git checkout -b feature/new-ingestor

# Make changes and test
python -m pytest tests/
python scripts/unified_ingest.py spot_ohlcv --dry_run --pair_limit 5

# Submit pull request with:
# - Clear description of changes
# - Test coverage for new functionality
# - Updated documentation if needed
```

## 🚨 Troubleshooting

### Common Issues

1. **Rate Limiting**: Adjust `API_RATE_LIMIT_*` settings and `INGESTION_API_CALL_DELAY`
2. **Database Connections**: Check `S2_*` configuration and connection pool settings
3. **Memory Usage**: Reduce `INGESTION_BATCH_SIZE` and `INGESTION_PARALLEL_WORKERS`
4. **API Authentication**: Verify `CCDATA_API_KEY` is valid and has required permissions

### Debug Mode

```bash
# Enable debug logging
export LOG_LEVEL=DEBUG

# Run with detailed output
python scripts/unified_ingest.py spot_ohlcv --pair_limit 5 --enable_monitoring
```

### Getting Help

- Check the [troubleshooting section](README_UNIFIED_INGESTION.md#troubleshooting) in the unified ingestion guide
- Review logs in `logs/ingestion.log`
- Use `--dry_run` flag to test configurations without data ingestion
- Enable monitoring to get detailed performance and error information

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

## 🎯 Next Steps

1. **[Get Started](README_UNIFIED_INGESTION.md#quick-start)** - Follow the quick start guide to begin using the unified ingestion framework
2. **[Configure Your Environment](README_UNIFIED_INGESTION.md#installation-and-setup)** - Set up your database and API credentials
3. **[Run Your First Ingestion](README_UNIFIED_INGESTION.md#usage-patterns)** - Try ingesting some sample data
4. **[Set Up Monitoring](README_UNIFIED_INGESTION.md#monitoring-and-observability)** - Enable monitoring for production workloads
5. **[Schedule Regular Ingestion](README_UNIFIED_INGESTION.md#scheduling-and-automation)** - Automate your data pipeline

**Ready to get started?** Check out the **[📖 Unified Ingestion Guide](README_UNIFIED_INGESTION.md)** for detailed instructions and examples!