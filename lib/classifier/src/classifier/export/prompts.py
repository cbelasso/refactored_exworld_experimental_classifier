"""
Prompt Exporter

Exports prompts as Python files matching the original classifier format.

Output Structure:
    prompts/
    ├── __init__.py
    ├── stage1/
    │   ├── __init__.py
    │   └── category_detection.py
    └── stage2/
        ├── __init__.py
        ├── attendee_engagement_and_interaction.py
        ├── people.py
        └── ...
"""

from datetime import datetime
from pathlib import Path
import re
from typing import Optional

from ..content.interfaces import ContentProvider
from ..pipeline.interfaces import PipelineContext
from ..schemas.interfaces import SchemaFactory
from ..stages import (
    AttributeExtractionStage,
    CategoryDetectionStage,
    ElementExtractionStage,
)


def _sanitize_name(name: str) -> str:
    """Convert display name to valid Python identifier / folder name."""
    result = name.lower()
    result = result.replace("&", "and")
    result = result.replace("/", "_")
    result = result.replace(" ", "_")
    result = result.replace("-", "_")
    result = re.sub(r"[^a-z0-9_]", "", result)
    result = re.sub(r"_+", "_", result)
    return result.strip("_")


class PromptExporter:
    """
    Exports prompts as Python files for the classifier.

    Generates:
    - stage1/category_detection.py with build_stage1_prompt()
    - stage2/{category}.py with build_stage2_prompt()
    """

    def __init__(self, content: ContentProvider, schema_factory: SchemaFactory):
        self.content = content
        self.schema_factory = schema_factory

    def export_prompts(self, output_dir: str | Path, verbose: bool = True) -> dict:
        """
        Export prompts as Python files.

        Args:
            output_dir: Output directory (will create prompts/ structure inside)
            verbose: Print progress

        Returns:
            Dict with export stats
        """
        output_dir = Path(output_dir)
        prompts_dir = output_dir / "prompts"
        prompts_dir.mkdir(parents=True, exist_ok=True)

        files_created = []

        # Create main __init__.py
        self._write_file(prompts_dir / "__init__.py", self._generate_main_init())
        files_created.append(prompts_dir / "__init__.py")

        # Stage 1
        stage1_dir = prompts_dir / "stage1"
        stage1_dir.mkdir(exist_ok=True)

        self._write_file(stage1_dir / "__init__.py", self._generate_stage1_init())
        files_created.append(stage1_dir / "__init__.py")

        stage1_content = self._generate_stage1_prompt_file()
        self._write_file(stage1_dir / "category_detection.py", stage1_content)
        files_created.append(stage1_dir / "category_detection.py")

        if verbose:
            print("✓ stage1/category_detection.py")

        # Stage 2
        stage2_dir = prompts_dir / "stage2"
        stage2_dir.mkdir(exist_ok=True)

        stage2_imports = []
        categories = self.content.get_categories()

        for cat in categories:
            cat_filename = _sanitize_name(cat.name)
            stage2_content = self._generate_stage2_prompt_file(cat.name)
            self._write_file(stage2_dir / f"{cat_filename}.py", stage2_content)
            files_created.append(stage2_dir / f"{cat_filename}.py")
            stage2_imports.append((cat_filename, cat.name))

            if verbose:
                print(f"✓ stage2/{cat_filename}.py")

        self._write_file(stage2_dir / "__init__.py", self._generate_stage2_init(stage2_imports))
        files_created.append(stage2_dir / "__init__.py")

        # Stage 3 (optional - per element)
        stage3_dir = prompts_dir / "stage3"
        stage3_dir.mkdir(exist_ok=True)

        stage3_imports = []
        for cat in categories:
            cat_filename = _sanitize_name(cat.name)
            cat_dir = stage3_dir / cat_filename
            cat_dir.mkdir(exist_ok=True)

            elements = self.content.get_elements(cat.name)
            elem_imports = []

            for elem in elements:
                elem_filename = _sanitize_name(elem.name)
                stage3_content = self._generate_stage3_prompt_file(cat.name, elem.name)
                self._write_file(cat_dir / f"{elem_filename}.py", stage3_content)
                files_created.append(cat_dir / f"{elem_filename}.py")
                elem_imports.append((elem_filename, elem.name))

                if verbose:
                    print(f"✓ stage3/{cat_filename}/{elem_filename}.py")

            self._write_file(
                cat_dir / "__init__.py", self._generate_stage3_category_init(elem_imports)
            )
            stage3_imports.append((cat_filename, cat.name))

        self._write_file(stage3_dir / "__init__.py", self._generate_stage3_init(stage3_imports))

        if verbose:
            print(f"\n✓ Exported {len(files_created)} files to {prompts_dir}")

        return {
            "output_dir": str(prompts_dir),
            "files_created": len(files_created),
        }

    def _write_file(self, path: Path, content: str) -> None:
        """Write content to file."""
        path.write_text(content, encoding="utf-8")

    def _generate_main_init(self) -> str:
        """Generate main prompts/__init__.py."""
        return f'''"""
Auto-generated prompt functions.
Generated: {datetime.now().isoformat()}
"""

from . import stage1
from . import stage2
from . import stage3

__all__ = ["stage1", "stage2", "stage3"]
'''

    def _generate_stage1_init(self) -> str:
        """Generate stage1/__init__.py."""
        return '''"""Stage 1: Category Detection prompts."""

from .category_detection import build_stage1_prompt, CATEGORIES

__all__ = ["build_stage1_prompt", "CATEGORIES"]
'''

    def _generate_stage2_init(self, imports: list) -> str:
        """Generate stage2/__init__.py."""
        lines = ['"""Stage 2: Element Extraction prompts."""', ""]

        for filename, _ in imports:
            lines.append(
                f"from .{filename} import build_stage2_prompt as build_{filename}_prompt"
            )

        lines.append("")
        lines.append("PROMPT_BUILDERS = {")
        for filename, cat_name in imports:
            lines.append(f'    "{cat_name}": build_{filename}_prompt,')
        lines.append("}")
        lines.append("")
        lines.append("def get_stage2_prompt_builder(category: str):")
        lines.append('    """Get the prompt builder for a category."""')
        lines.append("    return PROMPT_BUILDERS.get(category)")
        lines.append("")

        return "\n".join(lines)

    def _generate_stage3_init(self, imports: list) -> str:
        """Generate stage3/__init__.py."""
        lines = ['"""Stage 3: Attribute Extraction prompts."""', ""]

        for filename, _ in imports:
            lines.append(f"from . import {filename}")

        lines.append("")
        return "\n".join(lines)

    def _generate_stage3_category_init(self, imports: list) -> str:
        """Generate stage3/{category}/__init__.py."""
        lines = ['"""Element prompt builders."""', ""]

        for filename, _ in imports:
            lines.append(
                f"from .{filename} import build_stage3_prompt as build_{filename}_prompt"
            )

        lines.append("")
        lines.append("PROMPT_BUILDERS = {")
        for filename, elem_name in imports:
            lines.append(f'    "{elem_name}": build_{filename}_prompt,')
        lines.append("}")
        lines.append("")

        return "\n".join(lines)

    def _escape_string(self, s: str) -> str:
        """Escape string for use in Python code."""
        if not s:
            return ""
        return s.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")

    def _generate_stage1_prompt_file(self) -> str:
        """Generate stage1/category_detection.py."""
        categories = self.content.get_categories()
        examples = self.content.get_examples("stage1")
        rules = self.content.get_rules("stage1")

        # Build categories dict
        cat_lines = []
        for cat in categories:
            desc = self._escape_string(cat.description)
            cat_lines.append(f'    "{cat.name}": {{')
            cat_lines.append(f'        "description": "{desc}",')
            cat_lines.append(f'        "elements": {cat.elements},')
            cat_lines.append("    },")

        # Build examples
        example_lines = []
        for ex in examples[:10]:
            text = self._escape_string(ex.text)
            example_lines.append("    {")
            example_lines.append(f'        "text": "{text}",')
            example_lines.append(f'        "output": {ex.output},')
            if ex.explanation:
                expl = self._escape_string(ex.explanation)
                example_lines.append(f'        "explanation": "{expl}",')
            example_lines.append("    },")

        # Build rules
        rule_lines = []
        for r in rules[:10]:
            rule_text = self._escape_string(r.rule_text)
            rule_lines.append(f'    "{rule_text}",')

        return f'''"""
Stage 1: Category Detection Prompt
Auto-generated: {datetime.now().isoformat()}
"""

from typing import List


CATEGORIES = {{
{chr(10).join(cat_lines)}
}}

EXAMPLES = [
{chr(10).join(example_lines)}
]

RULES = [
{chr(10).join(rule_lines)}
]


def build_stage1_prompt(text: str, categories: dict = None) -> str:
    """
    Build the Stage 1 category detection prompt.
    
    Args:
        text: The text to classify
        categories: Optional category definitions (defaults to CATEGORIES)
    
    Returns:
        Formatted prompt string
    """
    categories = categories or CATEGORIES
    
    # Format categories table
    cat_table = []
    for name, info in categories.items():
        cat_table.append(f"- **{{name}}**: {{info['description']}}")
    categories_text = "\\n".join(cat_table)
    
    # Format rules
    rules_text = "\\n".join(f"- {{r}}" for r in RULES) if RULES else "None"
    
    # Format examples
    examples_text = ""
    for ex in EXAMPLES[:5]:
        examples_text += f"\\nText: {{ex['text'][:200]}}..."
        examples_text += f"\\nCategories: {{ex['output'].get('categories_present', [])}}"
        if ex.get('explanation'):
            examples_text += f"\\nReasoning: {{ex['explanation']}}"
        examples_text += "\\n"
    
    prompt = f"""You are a text classification system. Analyze the following text and identify which categories are present.

## Categories
{{categories_text}}

## Rules
{{rules_text}}

## Examples
{{examples_text}}

## Text to Analyze
{{text}}

## Instructions
Identify all categories that are present in the text. Return a JSON object with:
- categories_present: List of category names that are discussed in the text
- reasoning: Brief explanation of why these categories were selected

Valid category names: {{list(categories.keys())}}
"""
    return prompt


def get_valid_categories() -> List[str]:
    """Return list of valid category names."""
    return list(CATEGORIES.keys())
'''

    def _generate_stage2_prompt_file(self, category: str) -> str:
        """Generate stage2/{category}.py."""
        cat_sanitized = _sanitize_name(category)
        elements = self.content.get_elements(category)
        examples = self.content.get_examples("stage2", category=category)
        rules = self.content.get_rules("stage2", category=category)

        # Build elements dict
        elem_lines = []
        for elem in elements:
            desc = self._escape_string(elem.description)
            elem_lines.append(f'    "{elem.name}": {{')
            elem_lines.append(f'        "description": "{desc}",')
            elem_lines.append(f'        "attributes": {elem.attributes},')
            elem_lines.append("    },")

        # Build examples
        example_lines = []
        for ex in examples[:8]:
            text = self._escape_string(ex.text)
            example_lines.append("    {")
            example_lines.append(f'        "text": "{text}",')
            example_lines.append(f'        "output": {ex.output},')
            example_lines.append("    },")

        # Build rules
        rule_lines = []
        for r in rules[:10]:
            rule_text = self._escape_string(r.rule_text)
            rule_lines.append(f'    "{rule_text}",')

        return f'''"""
Stage 2: Element Extraction for {category}
Auto-generated: {datetime.now().isoformat()}
"""

from typing import List


CATEGORY = "{category}"

ELEMENTS = {{
{chr(10).join(elem_lines)}
}}

EXAMPLES = [
{chr(10).join(example_lines)}
]

RULES = [
{chr(10).join(rule_lines)}
]


def build_stage2_prompt(text: str, elements: dict = None) -> str:
    """
    Build the Stage 2 element extraction prompt for {category}.
    
    Args:
        text: The text to analyze
        elements: Optional element definitions (defaults to ELEMENTS)
    
    Returns:
        Formatted prompt string
    """
    elements = elements or ELEMENTS
    
    # Format elements table
    elem_table = []
    for name, info in elements.items():
        elem_table.append(f"- **{{name}}**: {{info['description']}}")
    elements_text = "\\n".join(elem_table)
    
    # Format rules
    rules_text = "\\n".join(f"- {{r}}" for r in RULES) if RULES else "None"
    
    prompt = f"""You are analyzing text for the category "{{CATEGORY}}".

## Elements to Detect
{{elements_text}}

## Rules
{{rules_text}}

## Text to Analyze
{{text}}

## Instructions
For each element that is discussed in the text, extract:
- element: The element name
- excerpt: The relevant text excerpt
- sentiment: One of "positive", "negative", "neutral", "mixed"
- confidence: 1-5 scale

Return a JSON object with an "elements" array.

Valid element names: {{list(elements.keys())}}
"""
    return prompt


def get_valid_elements() -> List[str]:
    """Return list of valid element names for {category}."""
    return list(ELEMENTS.keys())
'''

    def _generate_stage3_prompt_file(self, category: str, element: str) -> str:
        """Generate stage3/{category}/{element}.py."""
        attributes = self.content.get_attributes(category, element)
        examples = self.content.get_examples("stage3", category=category, element=element)
        rules = self.content.get_rules("stage3", category=category, element=element)

        # Build attributes dict
        attr_lines = []
        for attr in attributes:
            desc = self._escape_string(attr.description)
            attr_lines.append(f'    "{attr.name}": {{')
            attr_lines.append(f'        "description": "{desc}",')
            attr_lines.append("    },")

        # Build examples
        example_lines = []
        for ex in examples[:6]:
            text = self._escape_string(ex.text)
            example_lines.append("    {")
            example_lines.append(f'        "text": "{text}",')
            example_lines.append(f'        "output": {ex.output},')
            example_lines.append("    },")

        # Build rules
        rule_lines = []
        for r in rules[:8]:
            rule_text = self._escape_string(r.rule_text)
            rule_lines.append(f'    "{rule_text}",')

        return f'''"""
Stage 3: Attribute Extraction for {category} > {element}
Auto-generated: {datetime.now().isoformat()}
"""

from typing import List


CATEGORY = "{category}"
ELEMENT = "{element}"

ATTRIBUTES = {{
{chr(10).join(attr_lines)}
}}

EXAMPLES = [
{chr(10).join(example_lines)}
]

RULES = [
{chr(10).join(rule_lines)}
]


def build_stage3_prompt(text: str, attributes: dict = None) -> str:
    """
    Build the Stage 3 attribute extraction prompt for {element}.
    
    Args:
        text: The text/excerpt to analyze
        attributes: Optional attribute definitions (defaults to ATTRIBUTES)
    
    Returns:
        Formatted prompt string
    """
    attributes = attributes or ATTRIBUTES
    
    # Format attributes table
    attr_table = []
    for name, info in attributes.items():
        attr_table.append(f"- **{{name}}**: {{info['description']}}")
    attributes_text = "\\n".join(attr_table)
    
    # Format rules
    rules_text = "\\n".join(f"- {{r}}" for r in RULES) if RULES else "None"
    
    prompt = f"""You are analyzing text about "{{ELEMENT}}" in the category "{{CATEGORY}}".

## Attributes to Detect
{{attributes_text}}

## Rules
{{rules_text}}

## Text to Analyze
{{text}}

## Instructions
For each attribute mentioned in the text, extract:
- attribute: The attribute name
- excerpt: The relevant text excerpt
- sentiment: One of "positive", "negative", "neutral", "mixed"
- confidence: 1-5 scale

Return a JSON object with an "attributes" array.

Valid attribute names: {{list(attributes.keys())}}
"""
    return prompt


def get_valid_attributes() -> List[str]:
    """Return list of valid attribute names for {element}."""
    return list(ATTRIBUTES.keys())
'''

    # Keep old methods for backwards compatibility
    def export_hierarchical(self, output_dir: str | Path, verbose: bool = True) -> dict:
        """Alias for export_prompts for backwards compatibility."""
        return self.export_prompts(output_dir, verbose)

    def export_markdown_docs(self, output_path: str | Path) -> Path:
        """Export prompts as a single Markdown document for review."""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        lines = [
            "# Classification Prompts Reference",
            f"\nGenerated: {datetime.now().isoformat()}\n",
            "---\n",
        ]

        # Stage 1
        lines.append("## Stage 1: Category Detection\n")
        categories = self.content.get_categories()
        lines.append("### Categories\n")
        for cat in categories:
            lines.append(f"- **{cat.name}**: {cat.description}\n")

        examples = self.content.get_examples("stage1")
        if examples:
            lines.append("\n### Examples\n")
            for ex in examples[:5]:
                lines.append(f"**Text:** {ex.text[:200]}...\n")
                lines.append(f"**Output:** {ex.output}\n\n")

        # Stage 2
        lines.append("\n---\n")
        lines.append("## Stage 2: Element Extraction\n")

        for cat in categories:
            lines.append(f"\n### {cat.name}\n")
            elements = self.content.get_elements(cat.name)
            for elem in elements:
                lines.append(f"- **{elem.name}**: {elem.description}\n")

        output_path.write_text("\n".join(lines), encoding="utf-8")
        return output_path
