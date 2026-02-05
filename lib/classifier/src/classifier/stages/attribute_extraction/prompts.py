"""
Stage 3 Prompt Templates

Contains the prompt templates for attribute extraction.
Edit this file to modify how the LLM is instructed.
"""

import json
from typing import Any, Callable, List, Optional

from ...schemas.base import SentimentType


def build_attribute_extraction_prompt(
    text: str,
    category: str,
    element: str,
    element_sentiment: Optional[SentimentType],
    attributes: List[Any],
    examples: List[Any],
    rules: List[Any],
    valid_attribute_names: List[str],
    format_attributes: Callable,
    format_examples: Callable,
    format_rules: Callable,
) -> str:
    """
    Build the complete prompt for attribute extraction.

    Args:
        text: The feedback text to analyze
        category: The category context (from Stage 1)
        element: The element context (from Stage 2)
        element_sentiment: Overall element sentiment (from Stage 2)
        attributes: Attribute definitions for this element
        examples: Few-shot examples
        rules: Disambiguation rules
        valid_attribute_names: Valid attribute names for output
        format_attributes: Function to format attribute table
        format_examples: Function to format examples
        format_rules: Function to format rules

    Returns:
        Complete prompt string
    """

    # Format components
    attributes_section = format_attributes(attributes)
    examples_section = format_examples(examples) if examples else ""
    rules_section = format_rules(rules) if rules else ""

    # Sentiment context
    sentiment_str = element_sentiment.value if element_sentiment else "unknown"

    # Build output format
    output_format = _build_output_format(
        category, element, valid_attribute_names, sentiment_str
    )

    prompt = f"""You are an expert at analyzing conference feedback to identify specific attributes being discussed.

## Context
This feedback discusses: **{element}** (within {category})
Overall sentiment for this element: **{sentiment_str}**

Your task is to identify which specific ATTRIBUTES of "{element}" are discussed and their individual sentiments.

## Attributes of "{element}"
{attributes_section}

{rules_section}

## Examples
{examples_section}

## Output Format
{output_format}

## Text to Analyze
\"\"\"{text}\"\"\"

## Your Analysis
Identify the specific attributes discussed and their sentiments. Return valid JSON matching the format above."""

    return prompt


def _build_output_format(
    category: str,
    element: str,
    attribute_names: List[str],
    element_sentiment: str,
) -> str:
    """Build output format section."""

    example_attr = attribute_names[0] if attribute_names else "Example Attribute"

    example_output = {
        "category": category,
        "element": element,
        "element_sentiment": element_sentiment,
        "attributes": [
            {
                "attribute": example_attr,
                "sentiment": "positive",
                "confidence": 4,
                "excerpt": "relevant quote",
                "reasoning": "why this attribute is discussed",
            }
        ],
        "sentiment_consensus": True,
    }

    return f"""Return a JSON object with this structure:
```json
{json.dumps(example_output, indent=2)}
```

Valid attribute values for "{element}": {json.dumps(attribute_names)}

Sentiment values: "positive", "negative", "neutral", "mixed"
Confidence: 1-5

**sentiment_consensus**: Set to `true` if attribute sentiments generally agree with the element sentiment ({element_sentiment}), `false` if they significantly disagree.

Requirements:
- Only include attributes that are explicitly or implicitly discussed
- Extract relevant excerpts
- If no attributes clearly apply, return an empty attributes list"""


# =============================================================================
# Alternative Prompt Variants
# =============================================================================


def build_attribute_extraction_prompt_minimal(
    text: str,
    element: str,
    valid_attribute_names: List[str],
    element_sentiment: str,
) -> str:
    """
    Minimal variant for when attributes are few or well-defined.
    """
    attrs_str = ", ".join(valid_attribute_names)

    return f"""Analyze this feedback about "{element}" (overall sentiment: {element_sentiment}).

Attributes to check: {attrs_str}

Text: "{text}"

Return JSON with:
- element_sentiment: the overall sentiment
- attributes: list of {{attribute, sentiment, confidence, excerpt}}
- sentiment_consensus: true/false

Only include attributes explicitly discussed."""
