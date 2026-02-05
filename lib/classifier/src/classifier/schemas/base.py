"""
Base Schema Types

Common Pydantic models and types used across all stages.
These are STATIC schemas - for dynamic schemas, see factory.py.
"""

from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class SentimentType(str, Enum):
    """Sentiment values used throughout the pipeline."""

    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"
    MIXED = "mixed"


class ConfidenceLevel(int, Enum):
    """Confidence levels for classifications."""

    VERY_LOW = 1
    LOW = 2
    MEDIUM = 3
    HIGH = 4
    VERY_HIGH = 5


# =============================================================================
# Stage 1 Base Schemas
# =============================================================================


class CategoryDetection(BaseModel):
    """
    Base schema for a single category detection.

    Note: For dynamic Literal-constrained schemas, use SchemaFactory.
    """

    category: str
    is_present: bool
    confidence: int = Field(ge=1, le=5)
    reasoning: str = ""


class Stage1OutputBase(BaseModel):
    """Base output for Stage 1 (category detection)."""

    categories_present: List[str]
    reasoning: str = ""
    raw_text: Optional[str] = None


# =============================================================================
# Stage 2 Base Schemas
# =============================================================================


class ElementDetection(BaseModel):
    """Base schema for a single element detection."""

    element: str
    sentiment: SentimentType
    confidence: int = Field(ge=1, le=5)
    excerpt: str = ""
    reasoning: str = ""


class Stage2OutputBase(BaseModel):
    """Base output for Stage 2 (element extraction)."""

    category: str  # Which category this extraction is for
    elements: List[ElementDetection]
    raw_text: Optional[str] = None


# =============================================================================
# Stage 3 Base Schemas
# =============================================================================


class AttributeDetection(BaseModel):
    """Base schema for a single attribute detection."""

    attribute: str
    sentiment: SentimentType
    confidence: int = Field(ge=1, le=5)
    excerpt: str = ""
    reasoning: str = ""


class Stage3OutputBase(BaseModel):
    """Base output for Stage 3 (attribute extraction)."""

    category: str
    element: str
    element_sentiment: SentimentType  # Overall element sentiment
    attributes: List[AttributeDetection]
    sentiment_consensus: bool = True  # Whether attribute sentiments agree with element
    raw_text: Optional[str] = None


# =============================================================================
# Final Merged Output
# =============================================================================


class AttributeResult(BaseModel):
    """Final attribute in output."""

    name: str
    sentiment: SentimentType
    confidence: int
    excerpt: str = ""


class ElementResult(BaseModel):
    """Final element in output with nested attributes."""

    name: str
    sentiment: SentimentType
    confidence: int
    excerpt: str = ""
    attributes: List[AttributeResult] = []


class CategoryResult(BaseModel):
    """Final category in output with nested elements."""

    name: str
    elements: List[ElementResult] = []


class FinalClassificationOutput(BaseModel):
    """
    Complete classification result for a single text.

    Structure:
        text: "..."
        categories:
          - name: "People"
            elements:
              - name: "Speakers/Presenters"
                sentiment: "positive"
                attributes:
                  - name: "Knowledge"
                    sentiment: "positive"
    """

    text: str
    categories: List[CategoryResult]
    metadata: Optional[dict] = None
