"""
YAML Content Provider

Loads content from the YAML artifacts folder structure.

Folder Structure:
    artifacts/
    ├── _schema_ref.yaml
    ├── category_name/
    │   ├── _category.yaml
    │   ├── element_name/
    │   │   ├── _element.yaml
    │   │   ├── attribute_name.yaml
    │   │   └── ...
    │   └── ...
    └── ...

Usage:
    provider = YAMLContentProvider("path/to/artifacts")
    categories = provider.get_categories()
    examples = provider.get_examples("stage1")
"""

from pathlib import Path
import re
from typing import Any, Dict, List, Optional

import yaml

from ..interfaces import (
    AttributeContent,
    CategoryContent,
    ContentProvider,
    ElementContent,
    Example,
    Rule,
)


def _sanitize_folder_name(name: str) -> str:
    """Convert display name to folder name."""
    result = name.lower()
    result = result.replace("&", "and")
    result = result.replace("/", "_")
    result = result.replace(" ", "_")
    result = result.replace("-", "_")
    result = re.sub(r"[^a-z0-9_]", "", result)
    result = re.sub(r"_+", "_", result)
    result = result.strip("_")
    return result


def _load_yaml(filepath: Path) -> dict:
    """Load YAML file, returning empty dict if not found."""
    if not filepath.exists():
        return {}
    with open(filepath, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def _is_placeholder(text: str) -> bool:
    """Check if text is a placeholder comment."""
    return text.startswith("#") if text else True


class YAMLContentProvider(ContentProvider):
    """
    Loads content from YAML artifacts folder structure.

    This provider reads from the folder structure created by scaffold_artifacts()
    and optionally filled in by generate_artifact_content().

    Content is loaded lazily and cached.
    """

    def __init__(self, artifacts_dir: str | Path, verbose: bool = False):
        """
        Args:
            artifacts_dir: Path to artifacts directory
            verbose: Print loading progress
        """
        self.artifacts_dir = Path(artifacts_dir)
        self.verbose = verbose

        if not self.artifacts_dir.exists():
            raise FileNotFoundError(f"Artifacts directory not found: {artifacts_dir}")

        # Caches
        self._categories: Optional[List[CategoryContent]] = None
        self._elements: Dict[str, List[ElementContent]] = {}
        self._attributes: Dict[str, List[AttributeContent]] = {}
        self._category_examples: Optional[List[Example]] = None
        self._element_examples: Dict[str, List[Example]] = {}
        self._attribute_examples: Dict[str, List[Example]] = {}
        self._category_rules: Optional[List[Rule]] = None
        self._element_rules: Dict[str, List[Rule]] = {}
        self._attribute_rules: Dict[str, List[Rule]] = {}

        # Load structure
        self._load_structure()

    def _load_structure(self) -> None:
        """Load the folder structure and cache category/element/attribute names."""
        self._category_dirs: Dict[str, Path] = {}
        self._element_dirs: Dict[str, Dict[str, Path]] = {}
        self._attribute_files: Dict[str, Dict[str, Dict[str, Path]]] = {}

        for cat_dir in self.artifacts_dir.iterdir():
            if not cat_dir.is_dir() or cat_dir.name.startswith("_"):
                continue

            cat_yaml = cat_dir / "_category.yaml"
            if not cat_yaml.exists():
                continue

            cat_data = _load_yaml(cat_yaml)
            cat_name = cat_data.get("name", cat_dir.name)

            self._category_dirs[cat_name] = cat_dir
            self._element_dirs[cat_name] = {}
            self._attribute_files[cat_name] = {}

            for elem_dir in cat_dir.iterdir():
                if not elem_dir.is_dir() or elem_dir.name.startswith("_"):
                    continue

                elem_yaml = elem_dir / "_element.yaml"
                if not elem_yaml.exists():
                    continue

                elem_data = _load_yaml(elem_yaml)
                elem_name = elem_data.get("name", elem_dir.name)

                self._element_dirs[cat_name][elem_name] = elem_dir
                self._attribute_files[cat_name][elem_name] = {}

                for attr_file in elem_dir.iterdir():
                    if not attr_file.is_file() or attr_file.suffix != ".yaml":
                        continue
                    if attr_file.name.startswith("_"):
                        continue

                    attr_data = _load_yaml(attr_file)
                    attr_name = attr_data.get("name", attr_file.stem)
                    self._attribute_files[cat_name][elem_name][attr_name] = attr_file

        if self.verbose:
            print(f"Loaded structure: {len(self._category_dirs)} categories")

    def get_categories(self) -> List[CategoryContent]:
        """Get all category definitions."""
        if self._categories is not None:
            return self._categories

        self._categories = []

        for cat_name, cat_dir in self._category_dirs.items():
            cat_yaml = cat_dir / "_category.yaml"
            cat_data = _load_yaml(cat_yaml)

            self._categories.append(
                CategoryContent(
                    name=cat_name,
                    description=cat_data.get("description", ""),
                    condensed_description=cat_data.get("description", ""),
                    keywords=[],  # Could parse from description if needed
                    elements=list(self._element_dirs.get(cat_name, {}).keys()),
                )
            )

        return self._categories

    def get_elements(self, category: str) -> List[ElementContent]:
        """Get elements for a category."""
        if category in self._elements:
            return self._elements[category]

        elements = []
        elem_dirs = self._element_dirs.get(category, {})

        for elem_name, elem_dir in elem_dirs.items():
            elem_yaml = elem_dir / "_element.yaml"
            elem_data = _load_yaml(elem_yaml)

            attr_names = list(self._attribute_files.get(category, {}).get(elem_name, {}).keys())

            elements.append(
                ElementContent(
                    name=elem_name,
                    category=category,
                    description=elem_data.get("description", ""),
                    condensed_description=elem_data.get("description", ""),
                    keywords=[],
                    attributes=attr_names,
                )
            )

        self._elements[category] = elements
        return elements

    def get_attributes(self, category: str, element: str) -> List[AttributeContent]:
        """Get attributes for an element."""
        cache_key = f"{category}::{element}"
        if cache_key in self._attributes:
            return self._attributes[cache_key]

        attributes = []
        attr_files = self._attribute_files.get(category, {}).get(element, {})

        for attr_name, attr_file in attr_files.items():
            attr_data = _load_yaml(attr_file)

            attributes.append(
                AttributeContent(
                    name=attr_name,
                    element=element,
                    category=category,
                    description=attr_data.get("description", ""),
                    condensed_description=attr_data.get("description", ""),
                    keywords=[],
                )
            )

        self._attributes[cache_key] = attributes
        return attributes

    def get_examples(
        self,
        stage: str,
        category: Optional[str] = None,
        element: Optional[str] = None,
    ) -> List[Example]:
        """Get examples for a stage, optionally scoped."""

        if stage == "stage1":
            return self._get_category_examples()

        elif stage == "stage2":
            if category:
                return self._get_element_examples(category)
            # Return all element examples
            examples = []
            for cat_name in self._category_dirs:
                examples.extend(self._get_element_examples(cat_name))
            return examples

        elif stage == "stage3":
            if category and element:
                return self._get_attribute_examples(category, element)
            # Return all attribute examples
            examples = []
            for cat_name in self._category_dirs:
                for elem_name in self._element_dirs.get(cat_name, {}):
                    examples.extend(self._get_attribute_examples(cat_name, elem_name))
            return examples

        return []

    def _get_category_examples(self) -> List[Example]:
        """Get Stage 1 examples from _category.yaml files."""
        if self._category_examples is not None:
            return self._category_examples

        examples = []

        for cat_name, cat_dir in self._category_dirs.items():
            cat_yaml = cat_dir / "_category.yaml"
            cat_data = _load_yaml(cat_yaml)

            for ex in cat_data.get("examples", []):
                if not isinstance(ex, dict):
                    continue

                comment = ex.get("comment", "")
                if _is_placeholder(comment):
                    continue

                examples.append(
                    Example(
                        text=comment,
                        output={
                            "categories_present": [cat_name],
                            "reasoning": ex.get("reasoning", ""),
                        },
                        explanation=ex.get("reasoning", ""),
                        stage="stage1",
                        category=cat_name,
                    )
                )

        self._category_examples = examples
        return examples

    def _get_element_examples(self, category: str) -> List[Example]:
        """Get Stage 2 examples from _element.yaml files."""
        if category in self._element_examples:
            return self._element_examples[category]

        examples = []
        elem_dirs = self._element_dirs.get(category, {})

        for elem_name, elem_dir in elem_dirs.items():
            elem_yaml = elem_dir / "_element.yaml"
            elem_data = _load_yaml(elem_yaml)

            for ex in elem_data.get("examples", []):
                if not isinstance(ex, dict):
                    continue

                comment = ex.get("comment", "")
                excerpt = ex.get("excerpt", "")

                if _is_placeholder(comment) or _is_placeholder(excerpt):
                    continue

                examples.append(
                    Example(
                        text=comment,
                        output={
                            "element": elem_name,
                            "excerpt": excerpt,
                            "sentiment": ex.get("sentiment", "neutral"),
                            "reasoning": ex.get("reasoning", ""),
                        },
                        explanation=ex.get("reasoning", ""),
                        stage="stage2",
                        category=category,
                        element=elem_name,
                    )
                )

        self._element_examples[category] = examples
        return examples

    def _get_attribute_examples(self, category: str, element: str) -> List[Example]:
        """Get Stage 3 examples from attribute YAML files."""
        cache_key = f"{category}::{element}"
        if cache_key in self._attribute_examples:
            return self._attribute_examples[cache_key]

        examples = []
        attr_files = self._attribute_files.get(category, {}).get(element, {})

        for attr_name, attr_file in attr_files.items():
            attr_data = _load_yaml(attr_file)

            for ex in attr_data.get("examples", []):
                if not isinstance(ex, dict):
                    continue

                excerpt = ex.get("excerpt", "")
                if _is_placeholder(excerpt):
                    continue

                examples.append(
                    Example(
                        text=excerpt,
                        output={
                            "attribute": attr_name,
                            "sentiment": ex.get("sentiment", "neutral"),
                            "reasoning": ex.get("reasoning", ""),
                        },
                        explanation=ex.get("reasoning", ""),
                        stage="stage3",
                        category=category,
                        element=element,
                    )
                )

        self._attribute_examples[cache_key] = examples
        return examples

    def get_rules(
        self,
        stage: str,
        category: Optional[str] = None,
        element: Optional[str] = None,
    ) -> List[Rule]:
        """Get rules for a stage, optionally scoped."""

        if stage == "stage1":
            return self._get_category_rules()

        elif stage == "stage2":
            if category:
                return self._get_element_rules(category)
            rules = []
            for cat_name in self._category_dirs:
                rules.extend(self._get_element_rules(cat_name))
            return rules

        elif stage == "stage3":
            if category and element:
                return self._get_attribute_rules(category, element)
            rules = []
            for cat_name in self._category_dirs:
                for elem_name in self._element_dirs.get(cat_name, {}):
                    rules.extend(self._get_attribute_rules(cat_name, elem_name))
            return rules

        return []

    def _get_category_rules(self) -> List[Rule]:
        """Get Stage 1/2 rules from _category.yaml files."""
        if self._category_rules is not None:
            return self._category_rules

        rules = []

        for cat_name, cat_dir in self._category_dirs.items():
            cat_yaml = cat_dir / "_category.yaml"
            cat_data = _load_yaml(cat_yaml)

            for rule_text in cat_data.get("rules", []):
                if not isinstance(rule_text, str) or _is_placeholder(rule_text):
                    continue

                rules.append(
                    Rule(
                        rule_text=rule_text,
                        stage="stage1",
                        category=cat_name,
                    )
                )

        self._category_rules = rules
        return rules

    def _get_element_rules(self, category: str) -> List[Rule]:
        """Get Stage 2/3 rules from _element.yaml files."""
        if category in self._element_rules:
            return self._element_rules[category]

        rules = []
        elem_dirs = self._element_dirs.get(category, {})

        for elem_name, elem_dir in elem_dirs.items():
            elem_yaml = elem_dir / "_element.yaml"
            elem_data = _load_yaml(elem_yaml)

            for rule_text in elem_data.get("rules", []):
                if not isinstance(rule_text, str) or _is_placeholder(rule_text):
                    continue

                rules.append(
                    Rule(
                        rule_text=rule_text,
                        stage="stage2",
                        category=category,
                        element=elem_name,
                    )
                )

        self._element_rules[category] = rules
        return rules

    def _get_attribute_rules(self, category: str, element: str) -> List[Rule]:
        """Get Stage 3 rules from attribute YAML files."""
        cache_key = f"{category}::{element}"
        if cache_key in self._attribute_rules:
            return self._attribute_rules[cache_key]

        rules = []
        attr_files = self._attribute_files.get(category, {}).get(element, {})

        for attr_name, attr_file in attr_files.items():
            attr_data = _load_yaml(attr_file)

            for rule_text in attr_data.get("rules", []):
                if not isinstance(rule_text, str) or _is_placeholder(rule_text):
                    continue

                rules.append(
                    Rule(
                        rule_text=rule_text,
                        stage="stage3",
                        category=category,
                        element=element,
                    )
                )

        self._attribute_rules[cache_key] = rules
        return rules

    def clear_cache(self) -> None:
        """Clear all caches (call if YAML files change)."""
        self._categories = None
        self._elements.clear()
        self._attributes.clear()
        self._category_examples = None
        self._element_examples.clear()
        self._attribute_examples.clear()
        self._category_rules = None
        self._element_rules.clear()
        self._attribute_rules.clear()
