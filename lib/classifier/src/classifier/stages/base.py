"""
Base Stage Implementation

Provides common functionality for all stages:
- Content and schema factory access
- Prompt building utilities
- Logging helpers

Individual stages extend this base and implement their specific logic.
"""

from abc import abstractmethod
from typing import Any, Dict, List, Optional, Type

from pydantic import BaseModel

from ..content.interfaces import ContentProvider
from ..infrastructure.llm.interfaces import LLMClient
from ..pipeline.interfaces import PipelineContext, Stage
from ..schemas.interfaces import SchemaFactory


class BaseStage(Stage):
    """
    Base class for classification stages.

    Provides:
    - Content provider access
    - Schema factory access
    - Prompt export support
    - Common utilities

    Subclasses implement:
    - name property
    - dependencies property (if any)
    - process() method
    - build_prompt() method
    """

    def __init__(
        self,
        content: ContentProvider,
        schema_factory: SchemaFactory,
    ):
        """
        Args:
            content: Provider for examples, rules, descriptions
            schema_factory: Factory for Pydantic schemas
        """
        self.content = content
        self.schema_factory = schema_factory

    @property
    @abstractmethod
    def name(self) -> str:
        """Stage identifier."""
        pass

    @property
    def dependencies(self) -> List[str]:
        """Stages that must run before this one."""
        return []

    @abstractmethod
    def process(
        self,
        texts: List[str],
        context: PipelineContext,
        llm: LLMClient,
    ) -> Dict[str, Any]:
        """Process texts and return results."""
        pass

    @abstractmethod
    def build_prompt(
        self,
        text: str,
        context: Optional[PipelineContext] = None,
        **kwargs,
    ) -> str:
        """
        Build the prompt for a single text.

        This method is used both for processing and for export.
        """
        pass

    def get_prompt_for_export(
        self,
        text: str,
        context: PipelineContext,
    ) -> Optional[str]:
        """Get prompt for export (implements Stage interface)."""
        return self.build_prompt(text, context)

    # =========================================================================
    # Utility Methods
    # =========================================================================

    def format_examples(self, examples: List[Any], indent: int = 2) -> str:
        """Format examples for inclusion in prompts."""
        if not examples:
            return "No examples provided."

        lines = []
        indent_str = " " * indent

        for i, example in enumerate(examples, 1):
            lines.append(f"{indent_str}Example {i}:")
            lines.append(f'{indent_str}  Input: "{example.text}"')

            if hasattr(example, "output"):
                output = example.output
                if isinstance(output, dict):
                    import json

                    output_str = json.dumps(output, indent=4)
                    # Indent each line
                    output_lines = output_str.split("\n")
                    output_str = f"\n{indent_str}    ".join(output_lines)
                    lines.append(f"{indent_str}  Output: {output_str}")
                else:
                    lines.append(f"{indent_str}  Output: {output}")

            if hasattr(example, "explanation") and example.explanation:
                lines.append(f"{indent_str}  Explanation: {example.explanation}")

            lines.append("")  # Blank line between examples

        return "\n".join(lines)

    def format_rules(self, rules: List[Any]) -> str:
        """Format rules for inclusion in prompts."""
        if not rules:
            return ""

        lines = ["Rules and Guidelines:"]
        for rule in rules:
            rule_text = rule.rule_text if hasattr(rule, "rule_text") else str(rule)
            lines.append(f"  • {rule_text}")

        return "\n".join(lines)

    def format_categories_table(self, categories: List[Any]) -> str:
        """Format categories as a readable table."""
        lines = []
        for cat in categories:
            name = cat.name if hasattr(cat, "name") else str(cat)
            desc = getattr(cat, "condensed_description", "") or getattr(cat, "description", "")
            keywords = getattr(cat, "keywords", [])

            lines.append(f"• **{name}**")
            if desc:
                lines.append(f"  Description: {desc}")
            if keywords:
                lines.append(f"  Keywords: {', '.join(keywords)}")
            lines.append("")

        return "\n".join(lines)

    def format_elements_table(self, elements: List[Any]) -> str:
        """Format elements as a readable table."""
        lines = []
        for elem in elements:
            name = elem.name if hasattr(elem, "name") else str(elem)
            desc = getattr(elem, "condensed_description", "") or getattr(
                elem, "description", ""
            )
            keywords = getattr(elem, "keywords", [])

            lines.append(f"• **{name}**")
            if desc:
                lines.append(f"  Description: {desc}")
            if keywords:
                lines.append(f"  Keywords: {', '.join(keywords)}")
            lines.append("")

        return "\n".join(lines)

    def format_attributes_table(self, attributes: List[Any]) -> str:
        """Format attributes as a readable table."""
        lines = []
        for attr in attributes:
            name = attr.name if hasattr(attr, "name") else str(attr)
            desc = getattr(attr, "condensed_description", "") or getattr(
                attr, "description", ""
            )

            lines.append(f"• **{name}**")
            if desc:
                lines.append(f"  Description: {desc}")

        return "\n".join(lines)
