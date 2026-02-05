"""
Schemas Module

Contains Pydantic models for structured LLM output.

Static Schemas (base.py):
    - SentimentType, ConfidenceLevel
    - Stage output base classes
    - FinalClassificationOutput

Dynamic Schema Factory (factory.py):
    - TaxonomySchemaFactory - builds schemas with Literal constraints
    - Utilities for schema inspection

Usage:
    from refactored_classifier.schemas import TaxonomySchemaFactory, SentimentType

    factory = TaxonomySchemaFactory(content_provider)
    Stage1Schema = factory.get_stage1_schema()
"""

from .base import (
    AttributeDetection,
    AttributeResult,
    CategoryDetection,
    CategoryResult,
    ConfidenceLevel,
    ElementDetection,
    ElementResult,
    FinalClassificationOutput,
    SentimentType,
    Stage1OutputBase,
    Stage2OutputBase,
    Stage3OutputBase,
)
from .factory import (
    TaxonomySchemaFactory,
    get_valid_values,
    schema_to_json_example,
)
from .interfaces import SchemaFactory

__all__ = [
    # Base types
    "SentimentType",
    "ConfidenceLevel",
    # Stage schemas
    "CategoryDetection",
    "Stage1OutputBase",
    "ElementDetection",
    "Stage2OutputBase",
    "AttributeDetection",
    "Stage3OutputBase",
    # Final output
    "AttributeResult",
    "ElementResult",
    "CategoryResult",
    "FinalClassificationOutput",
    # Factory
    "TaxonomySchemaFactory",
    "get_valid_values",
    "schema_to_json_example",
]
