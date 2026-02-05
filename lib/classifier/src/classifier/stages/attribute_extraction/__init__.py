"""
Stage 3: Attribute Extraction

Extracts specific attributes within each detected element.

Usage:
    from refactored_classifier.stages.attribute_extraction import AttributeExtractionStage

    stage = AttributeExtractionStage(content, schema_factory)
    results = stage.process(texts, context, llm)
"""

from .prompts import (
    build_attribute_extraction_prompt,
    build_attribute_extraction_prompt_minimal,
)
from .stage import AttributeExtractionStage, AttributeExtractionTask

__all__ = [
    "AttributeExtractionStage",
    "AttributeExtractionTask",
    "build_attribute_extraction_prompt",
    "build_attribute_extraction_prompt_minimal",
]
