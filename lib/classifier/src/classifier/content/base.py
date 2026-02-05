"""
Base Content Provider and Composition Utilities

This module provides:
- CompositeContentProvider: Combine multiple providers with priority
- ContentOverrides: Apply partial overrides to a base provider
"""

from typing import Any, Dict, List, Optional

from .interfaces import (
    AttributeContent,
    CategoryContent,
    ContentProvider,
    ElementContent,
    Example,
    Rule,
)


class CompositeContentProvider(ContentProvider):
    """
    Combines multiple content providers with priority ordering.

    Content is fetched from providers in order. The first provider
    that returns non-empty content wins.

    Use Case:
        # Handcrafted is primary, fall back to YAML, then generated
        content = CompositeContentProvider([
            handcrafted_provider,  # First priority
            yaml_provider,         # Second priority
            generated_provider,    # Last resort
        ])

    This enables the workflow:
    1. Start with generated content for bootstrapping
    2. Annotators edit YAML files
    3. Developers add handcrafted content for proven cases
    4. Handcrafted takes priority when present
    """

    def __init__(self, providers: List[ContentProvider]):
        """
        Args:
            providers: List of providers in priority order (first = highest)
        """
        if not providers:
            raise ValueError("At least one provider required")
        self.providers = providers

    def get_categories(self) -> List[CategoryContent]:
        """Get categories from the first provider that has them."""
        for provider in self.providers:
            categories = provider.get_categories()
            if categories:
                return categories
        return []

    def get_elements(self, category: str) -> List[ElementContent]:
        """Get elements from the first provider that has them."""
        for provider in self.providers:
            elements = provider.get_elements(category)
            if elements:
                return elements
        return []

    def get_attributes(self, category: str, element: str) -> List[AttributeContent]:
        """Get attributes from the first provider that has them."""
        for provider in self.providers:
            attributes = provider.get_attributes(category, element)
            if attributes:
                return attributes
        return []

    def get_examples(
        self,
        stage: str,
        category: Optional[str] = None,
        element: Optional[str] = None,
    ) -> List[Example]:
        """
        Get examples, preferring earlier providers.

        Note: Unlike other methods, examples are merged across providers
        to allow combining handcrafted and generated examples.
        """
        all_examples = []
        seen_texts = set()

        for provider in self.providers:
            examples = provider.get_examples(stage, category, element)
            for example in examples:
                # Deduplicate by text
                if example.text not in seen_texts:
                    all_examples.append(example)
                    seen_texts.add(example.text)

        return all_examples

    def get_rules(
        self,
        stage: str,
        category: Optional[str] = None,
        element: Optional[str] = None,
    ) -> List[Rule]:
        """Get rules, merged across providers."""
        all_rules = []
        seen_texts = set()

        for provider in self.providers:
            rules = provider.get_rules(stage, category, element)
            for rule in rules:
                if rule.rule_text not in seen_texts:
                    all_rules.append(rule)
                    seen_texts.add(rule.rule_text)

        return all_rules


class MergingContentProvider(ContentProvider):
    """
    Alternative composition: merge content from all providers.

    Unlike CompositeContentProvider (which uses first-wins priority),
    this provider merges content from all providers, with later
    providers potentially overriding earlier ones for same-named items.

    Use Case:
        # Base definitions + overrides
        content = MergingContentProvider([
            base_taxonomy_provider,
            custom_overrides_provider,
        ])
    """

    def __init__(self, providers: List[ContentProvider]):
        if not providers:
            raise ValueError("At least one provider required")
        self.providers = providers

    def get_categories(self) -> List[CategoryContent]:
        """Merge categories by name (later providers override)."""
        by_name: Dict[str, CategoryContent] = {}
        for provider in self.providers:
            for cat in provider.get_categories():
                by_name[cat.name] = cat
        return list(by_name.values())

    def get_elements(self, category: str) -> List[ElementContent]:
        """Merge elements by name."""
        by_name: Dict[str, ElementContent] = {}
        for provider in self.providers:
            for elem in provider.get_elements(category):
                by_name[elem.name] = elem
        return list(by_name.values())

    def get_attributes(self, category: str, element: str) -> List[AttributeContent]:
        """Merge attributes by name."""
        by_name: Dict[str, AttributeContent] = {}
        for provider in self.providers:
            for attr in provider.get_attributes(category, element):
                by_name[attr.name] = attr
        return list(by_name.values())

    def get_examples(
        self,
        stage: str,
        category: Optional[str] = None,
        element: Optional[str] = None,
    ) -> List[Example]:
        """Concatenate examples from all providers (deduplicated)."""
        all_examples = []
        seen_texts = set()
        for provider in self.providers:
            for example in provider.get_examples(stage, category, element):
                if example.text not in seen_texts:
                    all_examples.append(example)
                    seen_texts.add(example.text)
        return all_examples

    def get_rules(
        self,
        stage: str,
        category: Optional[str] = None,
        element: Optional[str] = None,
    ) -> List[Rule]:
        """Concatenate rules from all providers (deduplicated)."""
        all_rules = []
        seen_texts = set()
        for provider in self.providers:
            for rule in provider.get_rules(stage, category, element):
                if rule.rule_text not in seen_texts:
                    all_rules.append(rule)
                    seen_texts.add(rule.rule_text)
        return all_rules
