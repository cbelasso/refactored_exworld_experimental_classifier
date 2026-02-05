"""
Result Merger

Combines outputs from all stages into FinalClassificationOutput.

Usage:
    from refactored_classifier.pipeline.merger import ResultMerger

    merger = ResultMerger()
    final_results = merger.merge(context)
"""

from typing import Any, Dict, List, Optional

from ..pipeline.interfaces import PipelineContext
from ..schemas.base import (
    AttributeResult,
    CategoryResult,
    ElementResult,
    FinalClassificationOutput,
    SentimentType,
)


class ResultMerger:
    """
    Merges stage outputs into final classification results.

    Takes PipelineContext with results from:
    - category_detection (Stage 1)
    - element_extraction (Stage 2)
    - attribute_extraction (Stage 3) [optional]

    Produces FinalClassificationOutput for each text.
    """

    def merge(self, context: PipelineContext) -> Dict[str, FinalClassificationOutput]:
        """
        Merge all stage results into final outputs.

        Args:
            context: Pipeline context with stage results

        Returns:
            Dict mapping text -> FinalClassificationOutput
        """
        results = {}

        stage1_results = context.get_all_stage_results("category_detection")
        stage2_results = context.get_all_stage_results("element_extraction")
        stage3_results = context.get_all_stage_results("attribute_extraction")

        for text in stage1_results:
            results[text] = self._merge_single(
                text=text,
                stage1=stage1_results.get(text),
                stage2=stage2_results.get(text, {}),
                stage3=stage3_results.get(text, {}),
            )

        return results

    def _merge_single(
        self,
        text: str,
        stage1: Any,
        stage2: Dict[str, Any],
        stage3: Dict[str, Any],
    ) -> FinalClassificationOutput:
        """Merge results for a single text."""
        categories = []

        # Get detected categories from Stage 1
        categories_present = getattr(stage1, "categories_present", []) if stage1 else []

        for cat_name in categories_present:
            # Get Stage 2 results for this category
            cat_stage2 = stage2.get(cat_name)
            elements = []

            if cat_stage2:
                element_detections = getattr(cat_stage2, "elements", [])

                for elem_det in element_detections:
                    elem_name = getattr(elem_det, "element", None)
                    if not elem_name:
                        continue

                    elem_sentiment = getattr(elem_det, "sentiment", SentimentType.NEUTRAL)
                    elem_confidence = getattr(elem_det, "confidence", 3)
                    elem_excerpt = getattr(elem_det, "excerpt", "")

                    # Get Stage 3 results for this element
                    stage3_key = f"{cat_name}::{elem_name}"
                    elem_stage3 = stage3.get(stage3_key)
                    attributes = []

                    if elem_stage3:
                        attr_detections = getattr(elem_stage3, "attributes", [])

                        for attr_det in attr_detections:
                            attr_name = getattr(attr_det, "attribute", None)
                            if not attr_name:
                                continue

                            attributes.append(
                                AttributeResult(
                                    name=attr_name,
                                    sentiment=getattr(
                                        attr_det, "sentiment", SentimentType.NEUTRAL
                                    ),
                                    confidence=getattr(attr_det, "confidence", 3),
                                    excerpt=getattr(attr_det, "excerpt", ""),
                                )
                            )

                    elements.append(
                        ElementResult(
                            name=elem_name,
                            sentiment=elem_sentiment,
                            confidence=elem_confidence,
                            excerpt=elem_excerpt,
                            attributes=attributes,
                        )
                    )

            categories.append(
                CategoryResult(
                    name=cat_name,
                    elements=elements,
                )
            )

        return FinalClassificationOutput(
            text=text,
            categories=categories,
        )

    def to_flat_records(self, results: Dict[str, FinalClassificationOutput]) -> List[Dict]:
        """
        Convert results to flat records for DataFrame/CSV export.

        Each row = one attribute (or element if no attributes).
        """
        records = []

        for text, output in results.items():
            for cat in output.categories:
                if not cat.elements:
                    records.append(
                        {
                            "text": text,
                            "category": cat.name,
                            "element": None,
                            "element_sentiment": None,
                            "attribute": None,
                            "attribute_sentiment": None,
                        }
                    )
                    continue

                for elem in cat.elements:
                    if not elem.attributes:
                        records.append(
                            {
                                "text": text,
                                "category": cat.name,
                                "element": elem.name,
                                "element_sentiment": elem.sentiment.value
                                if elem.sentiment
                                else None,
                                "element_confidence": elem.confidence,
                                "element_excerpt": elem.excerpt,
                                "attribute": None,
                                "attribute_sentiment": None,
                            }
                        )
                        continue

                    for attr in elem.attributes:
                        records.append(
                            {
                                "text": text,
                                "category": cat.name,
                                "element": elem.name,
                                "element_sentiment": elem.sentiment.value
                                if elem.sentiment
                                else None,
                                "element_confidence": elem.confidence,
                                "attribute": attr.name,
                                "attribute_sentiment": attr.sentiment.value
                                if attr.sentiment
                                else None,
                                "attribute_confidence": attr.confidence,
                                "attribute_excerpt": attr.excerpt,
                            }
                        )

        return records
