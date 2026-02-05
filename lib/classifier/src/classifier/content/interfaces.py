"""Content provider interfaces and data types."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, List, Optional


@dataclass
class CategoryContent:
    name: str
    description: str
    condensed_description: str = ""
    keywords: List[str] = field(default_factory=list)
    elements: List[str] = field(default_factory=list)


@dataclass
class ElementContent:
    name: str
    category: str
    description: str
    condensed_description: str = ""
    keywords: List[str] = field(default_factory=list)
    attributes: List[str] = field(default_factory=list)


@dataclass
class AttributeContent:
    name: str
    element: str
    category: str
    description: str
    condensed_description: str = ""
    keywords: List[str] = field(default_factory=list)


@dataclass
class Example:
    text: str
    output: Any
    explanation: Optional[str] = None
    stage: Optional[str] = None
    category: Optional[str] = None
    element: Optional[str] = None


@dataclass
class Rule:
    rule_text: str
    stage: Optional[str] = None
    category: Optional[str] = None
    element: Optional[str] = None


class ContentProvider(ABC):
    """Provides content (descriptions, examples, rules) for prompt building."""

    @abstractmethod
    def get_categories(self) -> List[CategoryContent]:
        pass

    @abstractmethod
    def get_elements(self, category: str) -> List[ElementContent]:
        pass

    @abstractmethod
    def get_attributes(self, category: str, element: str) -> List[AttributeContent]:
        pass

    @abstractmethod
    def get_examples(
        self, stage: str, category: Optional[str] = None, element: Optional[str] = None
    ) -> List[Example]:
        pass

    @abstractmethod
    def get_rules(
        self, stage: str, category: Optional[str] = None, element: Optional[str] = None
    ) -> List[Rule]:
        pass

    def get_all_category_names(self) -> List[str]:
        return [c.name for c in self.get_categories()]

    def get_all_element_names(self, category: str) -> List[str]:
        return [e.name for e in self.get_elements(category)]

    def get_all_attribute_names(self, category: str, element: str) -> List[str]:
        return [a.name for a in self.get_attributes(category, element)]
