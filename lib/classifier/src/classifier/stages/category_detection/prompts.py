"""
Stage 1 Prompt Templates

Contains the prompt templates for category detection.
Edit this file to modify how the LLM is instructed.

The prompts use Python string formatting for clarity and maintainability.
No external templating engine required.
"""

import json
from typing import Any, Callable, List


def build_category_detection_prompt(
    text: str,
    categories: List[Any],
    examples: List[Any],
    rules: List[Any],
    valid_category_names: List[str],
    format_categories: Callable,
    format_examples: Callable,
    format_rules: Callable,
) -> str:
    """
    Build the complete prompt for category detection.

    Args:
        text: The feedback text to classify
        categories: Category definitions from content provider
        examples: Few-shot examples from content provider
        rules: Disambiguation rules from content provider
        valid_category_names: List of valid category names for output
        format_categories: Function to format category table
        format_examples: Function to format examples
        format_rules: Function to format rules

    Returns:
        Complete prompt string
    """

    # Format the components
    categories_section = format_categories(categories)
    examples_section = format_examples(examples) if examples else ""
    rules_section = format_rules(rules) if rules else ""

    # Build output format description
    output_format = _build_output_format(valid_category_names)

    # Assemble the full prompt
    prompt = f"""You are an expert at analyzing conference feedback to identify the main topics being discussed.

## Task
Analyze the provided feedback text and identify which categories it discusses as MAIN TOPICS.
A category should only be marked as present if it's a significant focus of the feedback, not just briefly mentioned.

## Categories
{categories_section}

{rules_section}

## Examples
{examples_section}

## Output Format
{output_format}

## Text to Analyze
\"\"\"{text}\"\"\"

## Your Analysis
Identify the categories present in this feedback. Return valid JSON matching the format above."""

    return prompt


def _build_output_format(category_names: List[str]) -> str:
    """Build the output format section showing expected JSON structure."""

    example_output = {
        "categories_present": category_names[:2]
        if len(category_names) >= 2
        else category_names,
        "reasoning": "Brief explanation of why these categories were detected",
    }

    return f"""Return a JSON object with this structure:
```json
{json.dumps(example_output, indent=2)}
```

Valid category values: {json.dumps(category_names)}

Requirements:
- categories_present: List of category names (use EXACT names from the list above)
- reasoning: Brief explanation of your classification
- Only include categories that are MAIN TOPICS, not passing mentions"""


# =============================================================================
# Alternative Prompt Variants (for experimentation)
# =============================================================================


def build_category_detection_prompt_concise(
    text: str,
    valid_category_names: List[str],
) -> str:
    """
    A more concise variant of the category detection prompt.

    Use this for testing or when context window is limited.
    """
    categories_str = ", ".join(valid_category_names)

    return f"""Identify the main topics in this conference feedback.

Categories: {categories_str}

Text: "{text}"

Return JSON with:
- categories_present: list of relevant categories
- reasoning: brief explanation

Only include categories that are main topics, not passing mentions."""


def build_category_detection_prompt_detailed(
    text: str,
    categories: List[Any],
    examples: List[Any],
    rules: List[Any],
    valid_category_names: List[str],
    format_categories: Callable,
    format_examples: Callable,
    format_rules: Callable,
) -> str:
    """
    A more detailed variant with explicit step-by-step instructions.

    Use this when precision is more important than speed.
    """
    categories_section = format_categories(categories)
    examples_section = format_examples(examples) if examples else ""
    rules_section = format_rules(rules) if rules else ""

    prompt = f"""You are an expert analyst specializing in conference feedback classification.

## Your Task
Carefully analyze the feedback text below and determine which categories it discusses as MAIN TOPICS.

## Step-by-Step Process
1. Read the entire feedback text carefully
2. For each category, consider: Is this a main focus of the feedback?
3. Look for keywords and phrases that indicate each category
4. Only mark a category as present if it's a significant topic
5. Provide brief reasoning for your classification

## Available Categories
{categories_section}

## Classification Rules
{rules_section}

## Examples of Correct Classification
{examples_section}

## Important Notes
- A category should be marked as present ONLY if it's a main topic
- Brief mentions or tangential references don't count
- Multiple categories can be present in the same text
- If no categories clearly apply, return an empty list

## The Feedback Text to Analyze
\"\"\"{text}\"\"\"

## Output Format
Return a JSON object:
{{
    "categories_present": ["list", "of", "category", "names"],
    "reasoning": "Brief explanation"
}}

Valid categories: {json.dumps(valid_category_names)}

Now analyze the text and provide your classification:"""

    return prompt
