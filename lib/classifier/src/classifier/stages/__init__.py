"""
Classification Stages Module

Each stage is a self-contained processing unit that:
- Has a unique name
- Declares its dependencies
- Owns its prompt templates
- Uses ContentProvider for content and SchemaFactory for schemas

Available Stages:
    - CategoryDetectionStage (Stage 1): Identify high-level categories
    - ElementExtractionStage (Stage 2): Extract elements within categories
    - AttributeExtractionStage (Stage 3): Extract attributes within elements

Base Classes:
    - BaseStage: Common functionality for all stages

Usage:
    from refactored_classifier.stages import (
        CategoryDetectionStage,
        ElementExtractionStage,
        AttributeExtractionStage,
    )

    stage1 = CategoryDetectionStage(content, schema_factory)
    stage2 = ElementExtractionStage(content, schema_factory)
    stage3 = AttributeExtractionStage(content, schema_factory)
"""

from .attribute_extraction import AttributeExtractionStage
from .base import BaseStage
from .category_detection import CategoryDetectionStage
from .element_extraction import ElementExtractionStage

__all__ = [
    "BaseStage",
    "CategoryDetectionStage",
    "ElementExtractionStage",
    "AttributeExtractionStage",
]
