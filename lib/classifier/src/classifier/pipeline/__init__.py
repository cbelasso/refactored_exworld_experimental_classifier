"""
Pipeline Module

Coordinates the execution of classification stages.

Components:
    - StageRegistry: Manages stage registration and dependency resolution
    - PipelineOrchestrator: Runs stages in order
    - PipelineBuilder: Fluent builder for pipeline configuration

Usage:
    from refactored_classifier.pipeline import PipelineOrchestrator, StageRegistry

    # Using the builder
    from refactored_classifier.pipeline import PipelineBuilder

    pipeline = (
        PipelineBuilder()
        .with_content(content_provider)
        .with_llm(llm_client)
        .build()
    )

    results = pipeline.run(texts)
"""

from .interfaces import PipelineContext, Stage
from .merger import ResultMerger
from .orchestrator import PipelineBuilder, PipelineOrchestrator
from .registry import StageRegistry, create_default_registry

__all__ = [
    "Stage",
    "PipelineContext",
    "StageRegistry",
    "create_default_registry",
    "PipelineOrchestrator",
    "PipelineBuilder",
    "ResultMerger",
]
