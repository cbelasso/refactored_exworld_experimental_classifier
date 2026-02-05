"""
Dynamic Schema Factory

Builds Pydantic models at runtime with Literal types constrained to valid
taxonomy values. This ensures that LLM outputs are validated against the
actual taxonomy - invalid category/element/attribute names cause parse errors.

Key Feature:
    Instead of `category: str`, we generate `category: Literal["People", "Event Logistics", ...]`
    This catches hallucinated values at parse time.

Usage:
    content = HandcraftedContentProvider()
    factory = TaxonomySchemaFactory(content)

    # Get schema with categories constrained to actual taxonomy
    Stage1Schema = factory.get_stage1_schema()

    # Get schema for Stage 2 with elements constrained to "People" category
    Stage2Schema = factory.get_stage2_schema(category="People")
"""

from typing import Any, Dict, List, Literal, Optional, Type, get_args

from pydantic import BaseModel, Field, create_model

from ..content.interfaces import ContentProvider
from .base import SentimentType
from .interfaces import SchemaFactory


class TaxonomySchemaFactory(SchemaFactory):
    """
    Creates Pydantic schemas with Literal types from taxonomy content.

    This factory uses the ContentProvider to discover valid values,
    then builds schemas that constrain outputs to those values.
    """

    def __init__(self, content: ContentProvider):
        """
        Args:
            content: Provider that supplies taxonomy structure
        """
        self.content = content

        # Cache for generated schemas (avoid regenerating)
        self._stage1_schema: Optional[Type[BaseModel]] = None
        self._stage2_schemas: Dict[str, Type[BaseModel]] = {}
        self._stage3_schemas: Dict[str, Type[BaseModel]] = {}

    def get_stage1_schema(self) -> Type[BaseModel]:
        """
        Build Stage 1 schema with category names as Literal type.

        Returns a schema like:
            class Stage1Output(BaseModel):
                categories_present: List[Literal["People", "Event Logistics", ...]]
                reasoning: str
        """
        if self._stage1_schema is not None:
            return self._stage1_schema

        # Get valid category names
        category_names = self.content.get_all_category_names()

        if not category_names:
            raise ValueError("No categories found in content provider")

        # Create Literal type for categories
        CategoryLiteral = Literal[tuple(category_names)]  # type: ignore

        # Build the schema dynamically
        self._stage1_schema = create_model(
            "Stage1Output",
            categories_present=(List[CategoryLiteral], ...),  # type: ignore
            reasoning=(str, Field(default="")),
        )

        return self._stage1_schema

    def get_stage2_schema(self, category: str) -> Type[BaseModel]:
        """
        Build Stage 2 schema for a specific category.

        The element names are constrained to valid elements for that category.

        Returns a schema like:
            class Stage2Output_People(BaseModel):
                elements: List[ElementDetection]

            class ElementDetection(BaseModel):
                element: Literal["Speakers/Presenters", "Organizers", ...]
                sentiment: SentimentType
                confidence: int
        """
        if category in self._stage2_schemas:
            return self._stage2_schemas[category]

        # Get valid element names for this category
        element_names = self.content.get_all_element_names(category)

        if not element_names:
            raise ValueError(f"No elements found for category: {category}")

        # Create Literal type for elements
        ElementLiteral = Literal[tuple(element_names)]  # type: ignore

        # Create the element detection model
        ElementDetection = create_model(
            f"ElementDetection_{_safe_name(category)}",
            element=(ElementLiteral, ...),  # type: ignore
            sentiment=(SentimentType, ...),
            confidence=(int, Field(ge=1, le=5)),
            excerpt=(str, Field(default="")),
            reasoning=(str, Field(default="")),
        )

        # Create the stage output model
        schema = create_model(
            f"Stage2Output_{_safe_name(category)}",
            category=(Literal[category], category),  # type: ignore
            elements=(List[ElementDetection], ...),
        )

        self._stage2_schemas[category] = schema
        return schema

    def get_stage3_schema(self, category: str, element: str) -> Type[BaseModel]:
        """
        Build Stage 3 schema for a specific category/element pair.

        The attribute names are constrained to valid attributes for that element.
        """
        cache_key = f"{category}:{element}"
        if cache_key in self._stage3_schemas:
            return self._stage3_schemas[cache_key]

        # Get valid attribute names
        attribute_names = self.content.get_all_attribute_names(category, element)

        if not attribute_names:
            # If no attributes, return a simple schema
            schema = create_model(
                f"Stage3Output_{_safe_name(category)}_{_safe_name(element)}",
                category=(Literal[category], category),  # type: ignore
                element=(Literal[element], element),  # type: ignore
                element_sentiment=(SentimentType, ...),
                attributes=(List[Any], Field(default_factory=list)),
            )
            self._stage3_schemas[cache_key] = schema
            return schema

        # Create Literal type for attributes
        AttributeLiteral = Literal[tuple(attribute_names)]  # type: ignore

        # Create attribute detection model
        AttributeDetection = create_model(
            f"AttributeDetection_{_safe_name(category)}_{_safe_name(element)}",
            attribute=(AttributeLiteral, ...),  # type: ignore
            sentiment=(SentimentType, ...),
            confidence=(int, Field(ge=1, le=5)),
            excerpt=(str, Field(default="")),
            reasoning=(str, Field(default="")),
        )

        # Create stage output model
        schema = create_model(
            f"Stage3Output_{_safe_name(category)}_{_safe_name(element)}",
            category=(Literal[category], category),  # type: ignore
            element=(Literal[element], element),  # type: ignore
            element_sentiment=(SentimentType, ...),
            attributes=(List[AttributeDetection], ...),
            sentiment_consensus=(bool, True),
        )

        self._stage3_schemas[cache_key] = schema
        return schema

    def clear_cache(self) -> None:
        """Clear cached schemas (call if taxonomy changes)."""
        self._stage1_schema = None
        self._stage2_schemas.clear()
        self._stage3_schemas.clear()

    def get_all_stage2_schemas(self) -> Dict[str, Type[BaseModel]]:
        """Get Stage 2 schemas for all categories."""
        for category in self.content.get_all_category_names():
            self.get_stage2_schema(category)
        return self._stage2_schemas

    def get_all_stage3_schemas(self) -> Dict[str, Type[BaseModel]]:
        """Get Stage 3 schemas for all category/element pairs."""
        for category in self.content.get_all_category_names():
            for element in self.content.get_all_element_names(category):
                self.get_stage3_schema(category, element)
        return self._stage3_schemas


def _safe_name(name: str) -> str:
    """Convert a name to a valid Python identifier."""
    # Replace special characters with underscores
    safe = name.replace(" ", "_").replace("/", "_").replace("-", "_")
    safe = "".join(c for c in safe if c.isalnum() or c == "_")
    return safe


# =============================================================================
# Schema Inspection Utilities
# =============================================================================


def get_valid_values(schema: Type[BaseModel], field_name: str) -> List[str]:
    """
    Extract the valid Literal values for a field from a schema.

    Useful for prompt building and debugging.

    Usage:
        schema = factory.get_stage2_schema("People")
        # Get valid element names
        elements = get_valid_values(schema, "element")
        # -> ["Speakers/Presenters", "Organizers", ...]
    """
    field_info = schema.model_fields.get(field_name)
    if not field_info:
        return []

    annotation = field_info.annotation

    # Handle List[Literal[...]]
    if hasattr(annotation, "__origin__"):
        if annotation.__origin__ is list:
            inner = get_args(annotation)[0]
            if hasattr(inner, "__origin__") and inner.__origin__ is Literal:
                return list(get_args(inner))

    # Handle direct Literal[...]
    if hasattr(annotation, "__origin__") and annotation.__origin__ is Literal:
        return list(get_args(annotation))

    return []


def schema_to_json_example(schema: Type[BaseModel]) -> Dict[str, Any]:
    """
    Generate an example JSON structure from a schema.

    Useful for showing the expected output format in prompts.
    """
    example = {}

    for field_name, field_info in schema.model_fields.items():
        annotation = field_info.annotation

        # Get a representative value
        if hasattr(annotation, "__origin__"):
            if annotation.__origin__ is list:
                # List field - show one example item
                inner = get_args(annotation)[0]
                if hasattr(inner, "__origin__") and inner.__origin__ is Literal:
                    # List of Literals
                    values = get_args(inner)
                    example[field_name] = [values[0]] if values else []
                elif isinstance(inner, type) and issubclass(inner, BaseModel):
                    # List of nested models
                    example[field_name] = [schema_to_json_example(inner)]
                else:
                    example[field_name] = []
            elif annotation.__origin__ is Literal:
                # Literal field
                values = get_args(annotation)
                example[field_name] = values[0] if values else ""
        elif annotation is str:
            example[field_name] = ""
        elif annotation is int:
            example[field_name] = 3
        elif annotation is bool:
            example[field_name] = True
        elif isinstance(annotation, type) and issubclass(annotation, Enum):
            # Enum - use first value
            example[field_name] = list(annotation)[0].value
        else:
            example[field_name] = None

    return example
