"""
Stage 2: Element Extraction

Extracts specific elements within each detected category.

Usage:
    from refactored_classifier.stages.element_extraction import ElementExtractionStage

    stage = ElementExtractionStage(content, schema_factory)
    results = stage.process(texts, context, llm)
"""

from .prompts import (
    build_element_extraction_prompt,
    build_element_extraction_prompt_with_stage1_context,
)
from .stage import ElementExtractionStage, ElementExtractionTask

__all__ = [
    "ElementExtractionStage",
    "ElementExtractionTask",
    "build_element_extraction_prompt",
    "build_element_extraction_prompt_with_stage1_context",
]
