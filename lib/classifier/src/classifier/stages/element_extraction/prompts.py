"""
Stage 2 Prompt Templates

Contains the prompt templates for element extraction.
Edit this file to modify how the LLM is instructed.
"""

import json
from typing import Any, Callable, List


def build_element_extraction_prompt(
    text: str,
    category: str,
    elements: List[Any],
    examples: List[Any],
    rules: List[Any],
    valid_element_names: List[str],
    format_elements: Callable,
    format_examples: Callable,
    format_rules: Callable,
) -> str:
    """
    Build the complete prompt for element extraction.

    Args:
        text: The feedback text to analyze
        category: The category context (from Stage 1)
        elements: Element definitions for this category
        examples: Few-shot examples for this category
        rules: Disambiguation rules for this category
        valid_element_names: Valid element names for output
        format_elements: Function to format element table
        format_examples: Function to format examples
        format_rules: Function to format rules

    Returns:
        Complete prompt string
    """

    # Format components
    elements_section = format_elements(elements)
    examples_section = format_examples(examples) if examples else ""
    rules_section = format_rules(rules) if rules else ""

    # Build output format
    output_format = _build_output_format(category, valid_element_names)

    prompt = f"""You are an expert at analyzing conference feedback to identify specific elements being discussed.

## Context
This feedback has been categorized as relating to: **{category}**
Your task is to identify which specific elements within this category are discussed.

## Elements in "{category}"
{elements_section}

{rules_section}

## Examples
{examples_section}

## Output Format
{output_format}

## Text to Analyze
\"\"\"{text}\"\"\"

## Your Analysis
Identify which elements are discussed and their sentiment. Return valid JSON matching the format above."""

    return prompt


def _build_output_format(category: str, element_names: List[str]) -> str:
    """Build output format section."""

    example_element = element_names[0] if element_names else "Example Element"

    example_output = {
        "category": category,
        "elements": [
            {
                "element": example_element,
                "sentiment": "positive",
                "confidence": 4,
                "excerpt": "relevant quote from text",
                "reasoning": "why this element is present",
            }
        ],
    }

    return f"""Return a JSON object with this structure:
```json
{json.dumps(example_output, indent=2)}
```

Valid element values for "{category}": {json.dumps(element_names)}

Sentiment values: "positive", "negative", "neutral", "mixed"
Confidence: 1-5 (1=very uncertain, 5=very confident)

Requirements:
- Only include elements that are discussed as main topics
- Extract relevant excerpts that support your classification
- If no elements apply, return an empty elements list"""


# =============================================================================
# Alternative Prompt Variants
# =============================================================================


def build_element_extraction_prompt_with_stage1_context(
    text: str,
    category: str,
    elements: List[Any],
    examples: List[Any],
    rules: List[Any],
    valid_element_names: List[str],
    stage1_reasoning: str,
    format_elements: Callable,
    format_examples: Callable,
    format_rules: Callable,
) -> str:
    """
    Variant that includes Stage 1 reasoning for context.

    Use when you want Stage 2 to be informed by Stage 1's explanation.
    """
    elements_section = format_elements(elements)
    examples_section = format_examples(examples) if examples else ""
    rules_section = format_rules(rules) if rules else ""
    output_format = _build_output_format(category, valid_element_names)

    prompt = f"""You are an expert at analyzing conference feedback.

## Context from Previous Analysis
This feedback was categorized as relating to **{category}** with the following reasoning:
> {stage1_reasoning}

## Your Task
Now identify which specific elements within "{category}" are discussed.

## Elements in "{category}"
{elements_section}

{rules_section}

## Examples
{examples_section}

## Output Format
{output_format}

## Text to Analyze
\"\"\"{text}\"\"\"

## Your Analysis
Based on the category context above, identify the elements discussed:"""

    return prompt
