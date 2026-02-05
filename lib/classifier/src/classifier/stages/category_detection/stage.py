"""
Stage 1: Category Detection

Identifies which high-level categories are present in each text.

Input: Raw feedback texts
Output: List of detected categories per text

This is typically the first stage in the pipeline with no dependencies.

To Modify:
- Edit prompts.py to change LLM instructions
- Edit handcrafted content to add/change examples and rules
- The schema is dynamically built from taxonomy categories
"""

from typing import Any, Dict, List, Optional, Type

from pydantic import BaseModel

from ...content.interfaces import ContentProvider
from ...infrastructure.llm.interfaces import LLMClient
from ...pipeline.interfaces import PipelineContext
from ...schemas.interfaces import SchemaFactory
from ...stages.base import BaseStage
from .prompts import build_category_detection_prompt


class CategoryDetectionStage(BaseStage):
    """
    Stage 1: Detect which categories are discussed in each text.

    This stage has no dependencies - it can run on raw text.

    Output schema includes:
        - categories_present: List of category names (Literal-constrained)
        - reasoning: Brief explanation
    """

    @property
    def name(self) -> str:
        return "category_detection"

    @property
    def dependencies(self) -> List[str]:
        return []  # First stage, no dependencies

    def process(
        self,
        texts: List[str],
        context: PipelineContext,
        llm: LLMClient,
    ) -> Dict[str, Any]:
        """
        Detect categories for all texts.

        Uses batch processing for efficiency.
        """
        if not texts:
            return {}

        # Get the schema (with Literal-constrained category names)
        schema = self.schema_factory.get_stage1_schema()

        # Build prompts for all texts
        prompts = [self.build_prompt(text) for text in texts]
        schemas = [schema] * len(texts)

        # Batch LLM call
        responses = llm.batch_generate(prompts, schemas)

        # Map results back to texts
        results = {}
        for text, response in zip(texts, responses):
            results[text] = response.parsed

        return results

    def build_prompt(
        self,
        text: str,
        context: Optional[PipelineContext] = None,
        **kwargs,
    ) -> str:
        """
        Build the category detection prompt for a text.

        Assembles:
        - Task description
        - Category definitions from content provider
        - Examples from content provider
        - Rules from content provider
        - The actual text to classify
        """
        # Get content
        categories = self.content.get_categories()
        examples = self.content.get_examples(stage="stage1")
        rules = self.content.get_rules(stage="stage1")

        # Get valid category names (for the output format section)
        category_names = [cat.name for cat in categories]

        # Delegate to prompt builder
        return build_category_detection_prompt(
            text=text,
            categories=categories,
            examples=examples,
            rules=rules,
            valid_category_names=category_names,
            format_categories=self.format_categories_table,
            format_examples=self.format_examples,
            format_rules=self.format_rules,
        )
