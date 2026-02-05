"""
Stage 3: Attribute Extraction

Extracts specific attributes within each detected element.

Input: Texts + Stage 2 element extraction results
Output: Attributes with sentiment for each (text, category, element) tuple

Key Feature: Double Fan-out
    This stage creates one LLM call per (text, category, element) tuple.
    The fan-out is even wider than Stage 2.

Sentiment Consensus:
    This stage also tracks whether attribute-level sentiments agree with
    the element-level sentiment from Stage 2.

To Modify:
- Edit prompts.py to change LLM instructions
- Edit handcrafted content for examples/rules (or use generated content)
- Schema is dynamically built per (category, element) pair
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from pydantic import BaseModel

from ...content.interfaces import ContentProvider
from ...infrastructure.llm.interfaces import LLMClient
from ...pipeline.interfaces import PipelineContext
from ...schemas.base import SentimentType
from ...schemas.interfaces import SchemaFactory
from ...stages.base import BaseStage
from .prompts import build_attribute_extraction_prompt


@dataclass
class AttributeExtractionTask:
    """A single attribute extraction task (text + category + element)."""

    text: str
    category: str
    element: str
    element_sentiment: SentimentType  # From Stage 2
    element_excerpt: str = ""

    @property
    def key(self) -> str:
        return f"{self.text}:::{self.category}:::{self.element}"


class AttributeExtractionStage(BaseStage):
    """
    Stage 3: Extract attributes within detected elements.

    Depends on: element_extraction (Stage 2)

    This stage fans out per (text, category, element) - creating
    the finest-grained analysis in the pipeline.

    Output Structure:
        {
            text: {
                "category::element": AttributeExtractionResult,
                ...
            },
            ...
        }
    """

    @property
    def name(self) -> str:
        return "attribute_extraction"

    @property
    def dependencies(self) -> List[str]:
        return ["element_extraction"]

    def process(
        self,
        texts: List[str],
        context: PipelineContext,
        llm: LLMClient,
    ) -> Dict[str, Dict[str, Any]]:
        """
        Extract attributes for all texts and their detected elements.

        1. Build task list: (text, category, element) tuples from Stage 2
        2. Build prompts for each task
        3. Batch LLM call
        4. Aggregate results by text
        """
        # 1. Build task list from Stage 2 results
        tasks = self._build_tasks(texts, context)

        if not tasks:
            return {text: {} for text in texts}

        # 2. Build prompts and get schemas
        prompts = []
        schemas = []
        for task in tasks:
            prompt = self.build_prompt(
                text=task.text,
                context=context,
                category=task.category,
                element=task.element,
                element_sentiment=task.element_sentiment,
            )
            prompts.append(prompt)
            schemas.append(self.schema_factory.get_stage3_schema(task.category, task.element))

        # 3. Batch LLM call
        responses = llm.batch_generate(prompts, schemas)

        # 4. Aggregate results by text
        results: Dict[str, Dict[str, Any]] = {text: {} for text in texts}

        for task, response in zip(tasks, responses):
            key = f"{task.category}::{task.element}"
            results[task.text][key] = response.parsed

        return results

    def _build_tasks(
        self,
        texts: List[str],
        context: PipelineContext,
    ) -> List[AttributeExtractionTask]:
        """
        Build the list of (text, category, element) tasks from Stage 2 results.
        """
        tasks = []

        for text in texts:
            stage2_result = context.get_stage_result("element_extraction", text)

            if stage2_result is None:
                continue

            # Stage 2 result is Dict[category, ElementExtractionResult]
            for category, category_result in stage2_result.items():
                elements = getattr(category_result, "elements", [])

                for element_detection in elements:
                    element_name = getattr(element_detection, "element", None)
                    sentiment = getattr(element_detection, "sentiment", SentimentType.NEUTRAL)
                    excerpt = getattr(element_detection, "excerpt", "")

                    if element_name:
                        tasks.append(
                            AttributeExtractionTask(
                                text=text,
                                category=category,
                                element=element_name,
                                element_sentiment=sentiment,
                                element_excerpt=excerpt,
                            )
                        )

        return tasks

    def build_prompt(
        self,
        text: str,
        context: Optional[PipelineContext] = None,
        category: Optional[str] = None,
        element: Optional[str] = None,
        element_sentiment: Optional[SentimentType] = None,
        **kwargs,
    ) -> str:
        """
        Build attribute extraction prompt for a (text, category, element) tuple.
        """
        if category is None or element is None:
            raise ValueError("category and element are required for attribute extraction")

        # Get content for this element
        attributes = self.content.get_attributes(category, element)
        examples = self.content.get_examples(stage="stage3", category=category, element=element)
        rules = self.content.get_rules(stage="stage3", category=category, element=element)

        # Get valid attribute names
        attribute_names = [attr.name for attr in attributes]

        return build_attribute_extraction_prompt(
            text=text,
            category=category,
            element=element,
            element_sentiment=element_sentiment,
            attributes=attributes,
            examples=examples,
            rules=rules,
            valid_attribute_names=attribute_names,
            format_attributes=self.format_attributes_table,
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

        Returns prompts for all (category, element) pairs from Stage 2.
        """
        stage2_result = context.get_stage_result("element_extraction", text)

        if stage2_result is None:
            return None

        prompts = []
        for category, category_result in stage2_result.items():
            elements = getattr(category_result, "elements", [])

            for element_detection in elements:
                element_name = getattr(element_detection, "element", None)
                sentiment = getattr(element_detection, "sentiment", SentimentType.NEUTRAL)

                if element_name:
                    prompt = self.build_prompt(
                        text=text,
                        context=context,
                        category=category,
                        element=element_name,
                        element_sentiment=sentiment,
                    )
                    prompts.append(f"=== {category} > {element_name} ===\n\n{prompt}")

        if not prompts:
            return None

        return "\n\n" + "=" * 60 + "\n\n".join(prompts)
