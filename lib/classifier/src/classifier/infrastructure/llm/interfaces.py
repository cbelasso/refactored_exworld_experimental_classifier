"""LLM client interfaces."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, Generic, List, Optional, Type, TypeVar

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


@dataclass
class LLMResponse(Generic[T]):
    parsed: T
    raw_text: str = ""
    usage: Optional[Dict[str, int]] = None


class LLMClient(ABC):
    """Interface for LLM inference."""

    @abstractmethod
    def generate(
        self, prompt: str, schema: Type[T], temperature: float = 0.0
    ) -> LLMResponse[T]:
        pass

    @abstractmethod
    def batch_generate(
        self, prompts: List[str], schemas: List[Type[BaseModel]], temperature: float = 0.0
    ) -> List[LLMResponse]:
        pass
