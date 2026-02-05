"""
Stage 1: Category Detection

Identifies high-level categories present in feedback texts.

Usage:
    from refactored_classifier.stages.category_detection import CategoryDetectionStage

    stage = CategoryDetectionStage(content, schema_factory)
    results = stage.process(texts, context, llm)
"""

from .prompts import (
    build_category_detection_prompt,
    build_category_detection_prompt_concise,
    build_category_detection_prompt_detailed,
)
from .stage import CategoryDetectionStage

__all__ = [
    "CategoryDetectionStage",
    "build_category_detection_prompt",
    "build_category_detection_prompt_concise",
    "build_category_detection_prompt_detailed",
]
