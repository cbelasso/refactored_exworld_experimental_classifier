"""
Stage 2: Element Extraction

Extracts specific elements within each detected category.

Input: Texts + Stage 1 category detection results
Output: Elements with sentiment for each (text, category) pair

Key Feature: Fan-out
    This stage creates one LLM call per (text, category) pair.
    If a text has 3 categories detected, it generates 3 separate calls.

To Modify:
- Edit prompts.py to change LLM instructions
- Edit handcrafted content to add/change examples and rules
- Schema is dynamically built per category
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple, Type

from pydantic import BaseModel

from ...content.interfaces import ContentProvider
from ...infrastructure.llm.interfaces import LLMClient
from ...pipeline.interfaces import PipelineContext
from ...schemas.interfaces import SchemaFactory
from ...stages.base import BaseStage
from .prompts import build_element_extraction_prompt


@dataclass
class ElementExtractionTask:
    """A single element extraction task (text + category)."""

    text: str
    category: str

    @property
    def key(self) -> str:
        return f"{self.text}:::{self.category}"


class ElementExtractionStage(BaseStage):
    """
    Stage 2: Extract elements within detected categories.

    Depends on: category_detection (Stage 1)

    This stage "fans out" - for each text, it processes each
    detected category separately, allowing category-specific
    element definitions and examples.

    Output Structure:
        {
            text: {
                "category_name": ElementExtractionResult,
                ...
            },
            ...
        }
    """

    @property
    def name(self) -> str:
        return "element_extraction"

    @property
    def dependencies(self) -> List[str]:
        return ["category_detection"]

    def process(
        self,
        texts: List[str],
        context: PipelineContext,
        llm: LLMClient,
    ) -> Dict[str, Dict[str, Any]]:
        """
        Extract elements for all texts and their detected categories.

        1. Build task list: (text, category) pairs from Stage 1 results
        2. Build prompts for each task
        3. Batch LLM call
        4. Aggregate results by text
        """
        # 1. Build task list from Stage 1 results
        tasks = self._build_tasks(texts, context)

        if not tasks:
            # No categories detected, return empty results
            return {text: {} for text in texts}

        # 2. Build prompts and get schemas
        prompts = []
        schemas = []
        for task in tasks:
            prompt = self.build_prompt(
                text=task.text,
                context=context,
                category=task.category,
            )
            prompts.append(prompt)
            schemas.append(self.schema_factory.get_stage2_schema(task.category))

        # 3. Batch LLM call
        responses = llm.batch_generate(prompts, schemas)

        # 4. Aggregate results by text
        results: Dict[str, Dict[str, Any]] = {text: {} for text in texts}

        for task, response in zip(tasks, responses):
            results[task.text][task.category] = response.parsed

        return results

    def _build_tasks(
        self,
        texts: List[str],
        context: PipelineContext,
    ) -> List[ElementExtractionTask]:
        """
        Build the list of (text, category) tasks from Stage 1 results.
        """
        tasks = []

        for text in texts:
            stage1_result = context.get_stage_result("category_detection", text)

            if stage1_result is None:
                continue

            # Get categories present from Stage 1 result
            categories_present = getattr(stage1_result, "categories_present", [])

            for category in categories_present:
                tasks.append(
                    ElementExtractionTask(
                        text=text,
                        category=category,
                    )
                )

        return tasks

    def build_prompt(
        self,
        text: str,
        context: Optional[PipelineContext] = None,
        category: Optional[str] = None,
        **kwargs,
    ) -> str:
        """
        Build element extraction prompt for a (text, category) pair.

        Args:
            text: The feedback text
            context: Pipeline context (optional, for consistency)
            category: The category to extract elements for (REQUIRED)
        """
        if category is None:
            raise ValueError("category is required for element extraction prompt")

        # Get content for this category
        elements = self.content.get_elements(category)
        examples = self.content.get_examples(stage="stage2", category=category)
        rules = self.content.get_rules(stage="stage2", category=category)

        # Get valid element names for output format
        element_names = [elem.name for elem in elements]

        return build_element_extraction_prompt(
            text=text,
            category=category,
            elements=elements,
            examples=examples,
            rules=rules,
            valid_element_names=element_names,
            format_elements=self.format_elements_table,
            format_examples=self.format_examples,
            format_rules=self.format_rules,
        )

    def get_prompt_for_export(
        self,
        text: str,
        context: PipelineContext,
    ) -> Optional[str]:
        """
        Get prompts for export.

        Returns prompts for all categories detected in Stage 1.
        For multi-prompt export, returns them joined with separators.
        """
        stage1_result = context.get_stage_result("category_detection", text)

        if stage1_result is None:
            return None

        categories = getattr(stage1_result, "categories_present", [])

        if not categories:
            return None

        prompts = []
        for category in categories:
            prompt = self.build_prompt(text, context, category=category)
            prompts.append(f"=== Category: {category} ===\n\n{prompt}")

        return "\n\n" + "=" * 60 + "\n\n".join(prompts)
