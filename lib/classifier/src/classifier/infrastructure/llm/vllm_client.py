"""vLLM client implementation wrapping NewProcessor."""

from typing import Any, Dict, List, Optional, Type

from pydantic import BaseModel

from .interfaces import LLMClient, LLMResponse


class VLLMClient(LLMClient):
    """
    LLM client using vLLM via NewProcessor for multi-GPU parallel inference.

    Usage:
        from lib.utils.new_processor import NewProcessor

        processor = NewProcessor(
            gpu_list=[0, 1, 2, 3],
            llm="meta-llama/Llama-3.2-3B-Instruct",
            multiplicity=1,
        )

        llm = VLLMClient(processor)
        pipeline = PipelineBuilder().with_llm(llm).build()
    """

    def __init__(
        self,
        processor: Any,  # NewProcessor - using Any to avoid import dependency
        batch_size: int = 25,
        default_guided_config: Optional[Dict] = None,
    ):
        self.processor = processor
        self.batch_size = batch_size
        self.default_guided_config = default_guided_config or {
            "temperature": 0.1,
            "max_tokens": 1000,
        }

    def generate(
        self,
        prompt: str,
        schema: Type[BaseModel],
        temperature: float = 0.0,
    ) -> LLMResponse:
        """Generate a single structured response."""
        responses = self.batch_generate([prompt], [schema], temperature)
        return responses[0]

    def batch_generate(
        self,
        prompts: List[str],
        schemas: List[Type[BaseModel]],
        temperature: float = 0.0,
    ) -> List[LLMResponse]:
        """
        Generate responses for multiple prompts.

        Note: If all schemas are the same, uses single batch call.
        If schemas differ, groups by schema for efficient processing.
        """
        if not prompts:
            return []

        guided_config = {**self.default_guided_config, "temperature": temperature}

        # Check if all schemas are the same
        first_schema = schemas[0]
        all_same = all(s == first_schema for s in schemas)

        if all_same:
            return self._batch_single_schema(prompts, first_schema, guided_config)
        else:
            return self._batch_multiple_schemas(prompts, schemas, guided_config)

    def _batch_single_schema(
        self,
        prompts: List[str],
        schema: Type[BaseModel],
        guided_config: Dict,
    ) -> List[LLMResponse]:
        """Process all prompts with the same schema in one batch."""
        raw_responses = self.processor.process_with_schema(
            prompts=prompts,
            schema=schema,
            batch_size=self.batch_size,
            formatted=False,
            guided_config=guided_config,
        )

        parsed = self.processor.parse_results_with_schema(
            schema=schema,
            responses=raw_responses,
            validate=True,
        )

        return [
            LLMResponse(
                parsed=p if p is not None else self._create_fallback(schema),
                raw_text=str(p) if p else "",
            )
            for p in parsed
        ]

    def _batch_multiple_schemas(
        self,
        prompts: List[str],
        schemas: List[Type[BaseModel]],
        guided_config: Dict,
    ) -> List[LLMResponse]:
        """Process prompts with different schemas by grouping."""
        # Group by schema
        schema_groups: Dict[Type[BaseModel], List[tuple]] = {}
        for i, (prompt, schema) in enumerate(zip(prompts, schemas)):
            if schema not in schema_groups:
                schema_groups[schema] = []
            schema_groups[schema].append((i, prompt))

        # Process each group
        results = [None] * len(prompts)

        for schema, items in schema_groups.items():
            indices = [i for i, _ in items]
            group_prompts = [p for _, p in items]

            group_responses = self._batch_single_schema(group_prompts, schema, guided_config)

            for idx, response in zip(indices, group_responses):
                results[idx] = response

        return results

    def _create_fallback(self, schema: Type[BaseModel]) -> BaseModel:
        """Create a minimal valid instance when parsing fails."""
        try:
            return schema()
        except:
            # Try with empty/default values for required fields
            field_defaults = {}
            for name, field in schema.model_fields.items():
                if field.annotation == str:
                    field_defaults[name] = ""
                elif field.annotation == int:
                    field_defaults[name] = 0
                elif field.annotation == bool:
                    field_defaults[name] = False
                elif field.annotation == list or str(field.annotation).startswith("list"):
                    field_defaults[name] = []
            return schema.model_validate(field_defaults)


class VLLMClientFactory:
    """Factory for creating VLLMClient with NewProcessor."""

    @staticmethod
    def create(
        gpu_list: List[int],
        model: str = "meta-llama/Llama-3.2-3B-Instruct",
        multiplicity: int = 1,
        batch_size: int = 25,
        gpu_memory_utilization: float = 0.9,
        max_model_len: int = 2048,
        **processor_kwargs,
    ) -> VLLMClient:
        """
        Create a VLLMClient with a new NewProcessor instance.

        Usage:
            llm = VLLMClientFactory.create(
                gpu_list=[0, 1, 2, 3],
                model="meta-llama/Llama-3.2-3B-Instruct",
            )
        """
        # Import here to avoid dependency issues
        from lib.utils.new_processor import NewProcessor

        processor = NewProcessor(
            gpu_list=gpu_list,
            llm=model,
            multiplicity=multiplicity,
            gpu_memory_utilization=gpu_memory_utilization,
            max_model_len=max_model_len,
            **processor_kwargs,
        )

        return VLLMClient(processor, batch_size=batch_size)
