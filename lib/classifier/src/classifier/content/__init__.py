"""
Content Providers Module

Provides different sources of content for the classification pipeline.

Primary Provider:
    HandcraftedContentProvider - Battle-tested, manually curated content

Composition Utilities:
    CompositeContentProvider - Combine providers with priority
    MergingContentProvider - Merge content from multiple providers

Usage:
    from classifier.content import HandcraftedContentProvider, CompositeContentProvider

    # Use handcrafted only
    content = HandcraftedContentProvider()

    # Combine handcrafted (priority) with YAML (fallback)
    content = CompositeContentProvider([
        HandcraftedContentProvider(),
        YAMLContentProvider(artifacts_dir),
    ])
"""

from .base import CompositeContentProvider, MergingContentProvider
from .handcrafted.provider import HandcraftedContentProvider
from .interfaces import (
    AttributeContent,
    CategoryContent,
    ContentProvider,
    ElementContent,
    Example,
    Rule,
)
from .yaml.provider import YAMLContentProvider

__all__ = [
    # Interfaces
    "ContentProvider",
    "CategoryContent",
    "ElementContent",
    "AttributeContent",
    "Example",
    "Rule",
    # Providers
    "HandcraftedContentProvider",
    "YAMLContentProvider",
    # Composition utilities
    "CompositeContentProvider",
    "MergingContentProvider",
]
