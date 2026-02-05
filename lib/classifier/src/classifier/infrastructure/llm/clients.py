"""
LLM Client Implementations

Provides LLM clients for different backends:
- MockLLMClient: For testing without actual API calls
- (VLLMClient, OpenAIClient: Add as needed)

The LLMClient interface ensures all clients work the same way.
"""

import json
from typing import Any, Dict, List, Optional, Type

from pydantic import BaseModel

from .interfaces import LLMClient, LLMResponse


class MockLLMClient(LLMClient):
    """
    Mock LLM client for testing.

    Returns predefined responses or generates plausible mock data
    based on the schema.

    Usage:
        # With default mock behavior
        llm = MockLLMClient()

        # With predefined responses
        llm = MockLLMClient(responses={
            "prompt1": {"categories_present": ["People"]},
        })
    """

    def __init__(
        self,
        responses: Optional[Dict[str, Any]] = None,
        default_response: Optional[Dict[str, Any]] = None,
    ):
        """
        Args:
            responses: Dict mapping prompt substrings to responses
            default_response: Response to use when no match found
        """
        self.responses = responses or {}
        self.default_response = default_response
        self.call_history: List[Dict[str, Any]] = []

    def generate(
        self,
        prompt: str,
        schema: Type[BaseModel],
        temperature: float = 0.0,
    ) -> LLMResponse:
        """Generate a mock response."""
        # Record the call
        self.call_history.append(
            {
                "prompt": prompt,
                "schema": schema.__name__,
                "temperature": temperature,
            }
        )

        # Find matching response
        response_data = self._find_response(prompt)

        if response_data is None:
            # Generate mock data from schema
            response_data = self._generate_mock_from_schema(schema)

        # Parse into schema
        try:
            parsed = schema.model_validate(response_data)
        except Exception as e:
            # If validation fails, try to create a minimal valid instance
            parsed = self._create_minimal_instance(schema)

        return LLMResponse(
            parsed=parsed,
            raw_text=json.dumps(response_data),
        )

    def batch_generate(
        self,
        prompts: List[str],
        schemas: List[Type[BaseModel]],
        temperature: float = 0.0,
    ) -> List[LLMResponse]:
        """Generate mock responses for multiple prompts."""
        return [
            self.generate(prompt, schema, temperature)
            for prompt, schema in zip(prompts, schemas)
        ]

    def _find_response(self, prompt: str) -> Optional[Dict]:
        """Find a predefined response matching the prompt."""
        for key, response in self.responses.items():
            if key in prompt:
                return response
        return self.default_response

    def _generate_mock_from_schema(self, schema: Type[BaseModel]) -> Dict[str, Any]:
        """Generate mock data that matches the schema."""
        from pydantic_core import PydanticUndefined

        result = {}

        for field_name, field_info in schema.model_fields.items():
            annotation = field_info.annotation
            default = field_info.default

            # Use default if available and not undefined
            if default is not None and default is not PydanticUndefined and default != ...:
                result[field_name] = default
                continue

            # Generate based on type
            result[field_name] = self._mock_value_for_type(annotation, field_name)

        return result

    def _mock_value_for_type(self, annotation, field_name: str) -> Any:
        """Generate a mock value for a type annotation."""
        from typing import Literal, get_args, get_origin

        origin = get_origin(annotation)

        # Handle List types
        if origin is list:
            inner_args = get_args(annotation)
            if inner_args:
                inner_type = inner_args[0]
                inner_origin = get_origin(inner_type)

                # List[Literal[...]] - return list with first literal value
                if inner_origin is Literal:
                    literal_values = get_args(inner_type)
                    if literal_values:
                        return [literal_values[0]]

                # List[SomeModel] - return empty list
                return []
            return []

        # Handle Literal types directly
        if origin is Literal:
            literal_values = get_args(annotation)
            if literal_values:
                return literal_values[0]

        # Handle common cases
        if annotation is str:
            return f"mock_{field_name}"
        elif annotation is int:
            return 3
        elif annotation is bool:
            return True
        elif annotation is float:
            return 0.5

        # Handle Optional types
        if origin is type(None):
            return None

        # Enum types
        from enum import Enum

        if isinstance(annotation, type) and issubclass(annotation, Enum):
            return list(annotation)[0].value

        # Default
        return None

    def _create_minimal_instance(self, schema: Type[BaseModel]) -> BaseModel:
        """Create a minimal valid instance of the schema."""
        # Try with empty/default values
        try:
            return schema()
        except:
            pass

        # Try with mock values
        mock_data = self._generate_mock_from_schema(schema)
        return schema.model_validate(mock_data)

    def get_call_count(self) -> int:
        """Get the number of generate calls made."""
        return len(self.call_history)

    def clear_history(self) -> None:
        """Clear the call history."""
        self.call_history.clear()


class RecordingLLMClient(LLMClient):
    """
    Wrapper that records all calls to another LLM client.

    Useful for debugging and testing.

    Usage:
        real_llm = SomeLLMClient()
        recording_llm = RecordingLLMClient(real_llm)

        # Use recording_llm instead of real_llm
        result = recording_llm.generate(prompt, schema)

        # Inspect calls
        for call in recording_llm.calls:
            print(call["prompt"])
    """

    def __init__(self, wrapped: LLMClient):
        self.wrapped = wrapped
        self.calls: List[Dict[str, Any]] = []

    def generate(
        self,
        prompt: str,
        schema: Type[BaseModel],
        temperature: float = 0.0,
    ) -> LLMResponse:
        response = self.wrapped.generate(prompt, schema, temperature)

        self.calls.append(
            {
                "type": "generate",
                "prompt": prompt,
                "schema": schema.__name__,
                "temperature": temperature,
                "response": response.parsed.model_dump() if response.parsed else None,
            }
        )

        return response

    def batch_generate(
        self,
        prompts: List[str],
        schemas: List[Type[BaseModel]],
        temperature: float = 0.0,
    ) -> List[LLMResponse]:
        responses = self.wrapped.batch_generate(prompts, schemas, temperature)

        self.calls.append(
            {
                "type": "batch_generate",
                "prompts": prompts,
                "schemas": [s.__name__ for s in schemas],
                "temperature": temperature,
                "responses": [r.parsed.model_dump() if r.parsed else None for r in responses],
            }
        )

        return responses
