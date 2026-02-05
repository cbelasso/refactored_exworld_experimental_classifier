"""
Prompt Export Module

Exports prompts for review by annotators and developers.

Key Workflow:
1. Generate prompts from pipeline configuration
2. Export to files (one per category/element/attribute)
3. Annotators review and suggest changes
4. Developers update content providers based on feedback

Export Formats:
- Hierarchical: Organized by stage/category/element
- Flat: All prompts in one directory
- Markdown: Human-readable documentation
"""

from datetime import datetime
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..content.interfaces import ContentProvider
from ..pipeline.interfaces import PipelineContext
from ..schemas.interfaces import SchemaFactory
from ..stages import (
    AttributeExtractionStage,
    CategoryDetectionStage,
    ElementExtractionStage,
)


class PromptExporter:
    """
    Exports prompts for review and debugging.

    Usage:
        exporter = PromptExporter(content, schema_factory)

        # Export all prompts hierarchically
        exporter.export_hierarchical(output_dir="./exported_prompts")

        # Export prompts for specific texts
        exporter.export_for_texts(texts, output_dir="./prompts")
    """

    def __init__(
        self,
        content: ContentProvider,
        schema_factory: SchemaFactory,
    ):
        self.content = content
        self.schema_factory = schema_factory

        # Create stage instances for prompt building
        self.stage1 = CategoryDetectionStage(content, schema_factory)
        self.stage2 = ElementExtractionStage(content, schema_factory)
        self.stage3 = AttributeExtractionStage(content, schema_factory)

    def export_hierarchical(
        self,
        output_dir: str = "./exported_prompts",
        sample_text: str = "Sample feedback text for prompt generation.",
    ) -> Dict[str, str]:
        """
        Export prompts organized hierarchically by stage/category/element.

        Directory Structure:
            output_dir/
                stage1/
                    category_detection.txt
                stage2/
                    People/
                        element_extraction.txt
                    Event_Logistics/
                        element_extraction.txt
                stage3/
                    People/
                        Speakers_Presenters/
                            attribute_extraction.txt
                        Organizers/
                            attribute_extraction.txt
                    ...

        Args:
            output_dir: Root directory for export
            sample_text: Text to use in prompt examples

        Returns:
            Dict mapping file paths to their contents
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        exported_files = {}

        # Stage 1: Category Detection
        stage1_dir = output_path / "stage1"
        stage1_dir.mkdir(exist_ok=True)

        prompt = self.stage1.build_prompt(sample_text)
        file_path = stage1_dir / "category_detection.txt"
        file_path.write_text(prompt)
        exported_files[str(file_path)] = prompt

        # Stage 2: Element Extraction (one per category)
        stage2_dir = output_path / "stage2"
        stage2_dir.mkdir(exist_ok=True)

        for category in self.content.get_all_category_names():
            cat_dir = stage2_dir / _safe_filename(category)
            cat_dir.mkdir(exist_ok=True)

            prompt = self.stage2.build_prompt(
                sample_text,
                category=category,
            )
            file_path = cat_dir / "element_extraction.txt"
            file_path.write_text(prompt)
            exported_files[str(file_path)] = prompt

        # Stage 3: Attribute Extraction (one per category/element)
        stage3_dir = output_path / "stage3"
        stage3_dir.mkdir(exist_ok=True)

        for category in self.content.get_all_category_names():
            cat_dir = stage3_dir / _safe_filename(category)
            cat_dir.mkdir(exist_ok=True)

            for element in self.content.get_all_element_names(category):
                elem_dir = cat_dir / _safe_filename(element)
                elem_dir.mkdir(exist_ok=True)

                from ..schemas.base import SentimentType

                prompt = self.stage3.build_prompt(
                    sample_text,
                    category=category,
                    element=element,
                    element_sentiment=SentimentType.NEUTRAL,
                )
                file_path = elem_dir / "attribute_extraction.txt"
                file_path.write_text(prompt)
                exported_files[str(file_path)] = prompt

        # Write index file
        index_content = self._generate_index(exported_files, output_dir)
        index_path = output_path / "INDEX.md"
        index_path.write_text(index_content)
        exported_files[str(index_path)] = index_content

        return exported_files

    def export_for_texts(
        self,
        texts: List[str],
        output_dir: str = "./prompts_for_review",
        context: Optional[PipelineContext] = None,
    ) -> Dict[str, str]:
        """
        Export prompts for specific texts.

        Useful for debugging specific classification cases.

        Args:
            texts: Texts to generate prompts for
            output_dir: Output directory
            context: Optional context with prior stage results

        Returns:
            Dict mapping file paths to contents
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        exported_files = {}

        for i, text in enumerate(texts):
            text_dir = output_path / f"text_{i:03d}"
            text_dir.mkdir(exist_ok=True)

            # Save the original text
            text_file = text_dir / "input.txt"
            text_file.write_text(text)
            exported_files[str(text_file)] = text

            # Stage 1 prompt
            prompt = self.stage1.build_prompt(text)
            file_path = text_dir / "stage1_prompt.txt"
            file_path.write_text(prompt)
            exported_files[str(file_path)] = prompt

            # If we have context, generate stage 2/3 prompts too
            if context:
                stage1_result = context.get_stage_result("category_detection", text)
                if stage1_result:
                    categories = getattr(stage1_result, "categories_present", [])

                    for category in categories:
                        # Stage 2 prompt
                        prompt = self.stage2.build_prompt(text, category=category)
                        file_path = text_dir / f"stage2_{_safe_filename(category)}.txt"
                        file_path.write_text(prompt)
                        exported_files[str(file_path)] = prompt

        return exported_files

    def export_markdown_docs(
        self,
        output_file: str = "./prompt_documentation.md",
        sample_text: str = "Sample feedback text.",
    ) -> str:
        """
        Export all prompts as a single Markdown document.

        Great for sharing with annotators for review.
        """
        sections = []

        # Header
        sections.append("# Classification Prompt Documentation")
        sections.append(f"\nGenerated: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
        sections.append(
            "This document contains all prompts used in the classification pipeline.\n"
        )

        # Table of Contents
        sections.append("## Table of Contents\n")
        sections.append("1. [Stage 1: Category Detection](#stage-1-category-detection)")
        sections.append("2. [Stage 2: Element Extraction](#stage-2-element-extraction)")
        sections.append("3. [Stage 3: Attribute Extraction](#stage-3-attribute-extraction)")
        sections.append("")

        # Stage 1
        sections.append("---\n")
        sections.append("## Stage 1: Category Detection\n")
        sections.append("Identifies which high-level categories are discussed in feedback.\n")
        sections.append("### Prompt Template\n")
        sections.append("```")
        sections.append(self.stage1.build_prompt(sample_text))
        sections.append("```\n")

        # Stage 2
        sections.append("---\n")
        sections.append("## Stage 2: Element Extraction\n")
        sections.append("Extracts specific elements within each detected category.\n")

        for category in self.content.get_all_category_names():
            sections.append(f"### {category}\n")
            sections.append("```")
            sections.append(self.stage2.build_prompt(sample_text, category=category))
            sections.append("```\n")

        # Stage 3
        sections.append("---\n")
        sections.append("## Stage 3: Attribute Extraction\n")
        sections.append("Extracts specific attributes within each element.\n")

        from refactored_classifier.schemas.base import SentimentType

        for category in self.content.get_all_category_names():
            sections.append(f"### {category}\n")

            for element in self.content.get_all_element_names(category):
                sections.append(f"#### {element}\n")
                sections.append("```")
                sections.append(
                    self.stage3.build_prompt(
                        sample_text,
                        category=category,
                        element=element,
                        element_sentiment=SentimentType.NEUTRAL,
                    )
                )
                sections.append("```\n")

        content = "\n".join(sections)

        # Write file
        Path(output_file).write_text(content)

        return content

    def _generate_index(
        self,
        exported_files: Dict[str, str],
        output_dir: str,
    ) -> str:
        """Generate an index file for the exported prompts."""
        lines = [
            "# Exported Prompts Index",
            f"\nGenerated: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n",
            "## Files\n",
        ]

        # Group by stage
        stage1_files = []
        stage2_files = []
        stage3_files = []

        for path in sorted(exported_files.keys()):
            rel_path = path.replace(output_dir, "").lstrip("/")
            if "stage1" in path:
                stage1_files.append(rel_path)
            elif "stage2" in path:
                stage2_files.append(rel_path)
            elif "stage3" in path:
                stage3_files.append(rel_path)

        lines.append("### Stage 1: Category Detection\n")
        for f in stage1_files:
            lines.append(f"- [{f}]({f})")

        lines.append("\n### Stage 2: Element Extraction\n")
        for f in stage2_files:
            lines.append(f"- [{f}]({f})")

        lines.append("\n### Stage 3: Attribute Extraction\n")
        for f in stage3_files:
            lines.append(f"- [{f}]({f})")

        return "\n".join(lines)


def _safe_filename(name: str) -> str:
    """Convert a name to a safe filename."""
    return name.replace(" ", "_").replace("/", "_").replace("&", "and")
