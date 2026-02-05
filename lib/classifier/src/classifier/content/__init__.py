"""
Content Providers Module

Provides different sources of content for the classification pipeline.

Primary Provider:
    HandcraftedContentProvider - Battle-tested, manually curated content

Composition Utilities:
    CompositeContentProvider - Combine providers with priority
    MergingContentProvider - Merge content from multiple providers

Usage:
    from refactored_classifier.content import HandcraftedContentProvider

    content = HandcraftedContentProvider()
    categories = content.get_categories()
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
    "ContentProvider",
    "CategoryContent",
    "ElementContent",
    "AttributeContent",
    "Example",
    "Rule",
    "CompositeContentProvider",
    "MergingContentProvider",
    "HandcraftedContentProvider",
    "YAMLContentProvider",
]

__all__ = [
    "CompositeContentProvider",
    "MergingContentProvider",
    "HandcraftedContentProvider",
]
