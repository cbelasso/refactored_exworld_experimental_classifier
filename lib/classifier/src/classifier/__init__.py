"""
Refactored Classifier

A clean, modular multi-stage text classification system.

Quick Start:
    from refactored_classifier import (
        HandcraftedContentProvider,
        TaxonomySchemaFactory,
        PipelineBuilder,
        MockLLMClient,
    )

    # Setup
    content = HandcraftedContentProvider()
    llm = MockLLMClient()  # or your real LLM client

    # Build pipeline
    pipeline = (
        PipelineBuilder()
        .with_content(content)
        .with_llm(llm)
        .build()
    )

    # Run classification
    results = pipeline.run(["The speakers were excellent!"])

Architecture:
    - core/: Interfaces and base types
    - content/: Content providers (handcrafted, YAML, generated)
    - schemas/: Pydantic models and dynamic schema factory
    - stages/: Classification stages (category, element, attribute)
    - pipeline/: Orchestrator and registry
    - export/: Prompt export utilities
    - infrastructure/: LLM clients and external integrations

Design Principles:
    - Interface-driven: Clear contracts between components
    - Dependency injection: Easy to test and extend
    - Explicit over magic: No auto-discovery, clear registration
    - Content as data: Handcrafted content is primary, editable
"""

__version__ = "0.1.0"

# Content
# Export
# Schemas
from .content import (
    AttributeContent,
    CategoryContent,
    CompositeContentProvider,
    ContentProvider,
    ElementContent,
    Example,
    HandcraftedContentProvider,
    Rule,
)
from .export import PromptExporter

# Infrastructure
from .infrastructure.llm import LLMClient, LLMResponse, MockLLMClient

# Pipeline
from .pipeline import (
    PipelineBuilder,
    PipelineContext,
    PipelineOrchestrator,
    Stage,
    StageRegistry,
    create_default_registry,
)
from .schemas import (
    FinalClassificationOutput,
    SchemaFactory,
    SentimentType,
    TaxonomySchemaFactory,
)

# Stages
from .stages import (
    AttributeExtractionStage,
    CategoryDetectionStage,
    ElementExtractionStage,
)

__all__ = [
    "__version__",
    # Content
    "ContentProvider",
    "CategoryContent",
    "ElementContent",
    "AttributeContent",
    "Example",
    "Rule",
    "HandcraftedContentProvider",
    "CompositeContentProvider",
    # Schemas
    "SchemaFactory",
    "TaxonomySchemaFactory",
    "SentimentType",
    "FinalClassificationOutput",
    # Pipeline
    "Stage",
    "PipelineContext",
    "PipelineOrchestrator",
    "PipelineBuilder",
    "StageRegistry",
    "create_default_registry",
    # Stages
    "CategoryDetectionStage",
    "ElementExtractionStage",
    "AttributeExtractionStage",
    # Export
    "PromptExporter",
    # Infrastructure
    "LLMClient",
    "LLMResponse",
    "MockLLMClient",
]
