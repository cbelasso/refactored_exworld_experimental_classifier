"""
Export Module

Provides tools for exporting prompts and results for review.

Components:
    - PromptExporter: Export prompts for annotator review

Workflow:
1. Configure pipeline with content and schemas
2. Use PromptExporter to generate prompt files
3. Share with annotators for review
4. Incorporate feedback into content providers
5. Re-export and iterate

Usage:
    from refactored_classifier.export import PromptExporter

    exporter = PromptExporter(content, schema_factory)
    exporter.export_hierarchical("./prompts")
    exporter.export_markdown_docs("./docs/prompts.md")
"""

from .prompts import PromptExporter

__all__ = [
    "PromptExporter",
]
