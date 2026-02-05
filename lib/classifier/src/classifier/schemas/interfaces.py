"""Schema factory interface."""

from abc import ABC, abstractmethod
from typing import Type

from pydantic import BaseModel


class SchemaFactory(ABC):
    """Builds Pydantic schemas for LLM structured output."""

    @abstractmethod
    def get_stage1_schema(self) -> Type[BaseModel]:
        pass

    @abstractmethod
    def get_stage2_schema(self, category: str) -> Type[BaseModel]:
        pass

    @abstractmethod
    def get_stage3_schema(self, category: str, element: str) -> Type[BaseModel]:
        pass
