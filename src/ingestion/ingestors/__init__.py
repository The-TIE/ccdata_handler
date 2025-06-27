"""
Concrete ingestor implementations for the unified data ingestion pipeline.

This package contains specialized ingestor classes that extend the base
abstractions to handle specific data types and sources.
"""

from .spot_ohlcv_ingestor import SpotOHLCVIngestor
from .asset_metadata_ingestor import AssetMetadataIngestor
from .exchange_metadata_ingestor import ExchangeMetadataIngestor
from .indices_ohlcv_ingestor import IndicesOHLCVIngestor
from .futures_data_ingestor import FuturesDataIngestor
from .instrument_metadata_ingestor import InstrumentMetadataIngestor

__all__ = [
    "SpotOHLCVIngestor",
    "AssetMetadataIngestor",
    "ExchangeMetadataIngestor",
    "IndicesOHLCVIngestor",
    "FuturesDataIngestor",
    "InstrumentMetadataIngestor",
]
