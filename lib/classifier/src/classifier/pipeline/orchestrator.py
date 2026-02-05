"""
Pipeline Orchestrator

The thin coordination layer that runs stages in order.

Design Philosophy:
- This file should NEVER contain classification logic
- It just discovers stages, resolves order, and runs them
- All business logic lives in stages and content providers
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from ..infrastructure.llm.interfaces import LLMClient
from .interfaces import PipelineContext, Stage
from .registry import StageRegistry


class PipelineOrchestrator:
    """
    Runs stages in dependency order.

    This class knows nothing about categories, elements, or attributes.
    It just knows how to run Stage objects.

    Usage:
        orchestrator = PipelineOrchestrator(registry, llm)

        # Run full pipeline
        results = orchestrator.run(texts)

        # Run specific stages (dependencies auto-included)
        results = orchestrator.run(texts, stages=["category_detection"])
    """

    def __init__(
        self,
        registry: StageRegistry,
        llm: LLMClient,
        verbose: bool = True,
    ):
        """
        Args:
            registry: Stage registry with registered stages
            llm: LLM client for inference
            verbose: If True, print progress messages
        """
        self.registry = registry
        self.llm = llm
        self.verbose = verbose

    def run(
        self,
        texts: List[str],
        stages: Optional[List[str]] = None,
    ) -> Dict[str, Dict[str, Any]]:
        """
        Run the pipeline on texts.

        Args:
            texts: Texts to process
            stages: Stage names to run (None = all registered stages)
                    Dependencies are automatically included.

        Returns:
            Dict mapping text -> {stage_name -> stage_output}
        """
        # Resolve execution order
        execution_order = self.registry.resolve_order(stages)

        if self.verbose:
            self._log(f"Pipeline: {' → '.join(execution_order)}")
            self._log(f"Processing {len(texts)} texts")

        # Initialize context
        context = PipelineContext()
        context.set_metadata("start_time", datetime.now().isoformat())
        context.set_metadata("stages_requested", stages)
        context.set_metadata("stages_executed", execution_order)

        # Run each stage in order
        for stage_name in execution_order:
            stage = self.registry.get(stage_name)

            if self.verbose:
                self._log(f"Running: {stage_name}")

            start_time = datetime.now()

            # Process texts
            stage_results = stage.process(
                texts=texts,
                context=context,
                llm=self.llm,
            )

            # Store results in context for downstream stages
            context.set_stage_results(stage_name, stage_results)

            elapsed = (datetime.now() - start_time).total_seconds()

            if self.verbose:
                self._log(f"✓ {stage_name} complete ({elapsed:.2f}s)")

        context.set_metadata("end_time", datetime.now().isoformat())

        # Return merged results
        return context.get_merged_results()

    def run_with_context(
        self,
        texts: List[str],
        stages: Optional[List[str]] = None,
    ) -> PipelineContext:
        """
        Run pipeline and return the full context object.

        Use this when you need access to metadata or want to
        inspect intermediate results.
        """
        execution_order = self.registry.resolve_order(stages)

        context = PipelineContext()
        context.set_metadata("start_time", datetime.now().isoformat())

        for stage_name in execution_order:
            stage = self.registry.get(stage_name)

            if self.verbose:
                self._log(f"Running: {stage_name}")

            stage_results = stage.process(
                texts=texts,
                context=context,
                llm=self.llm,
            )

            context.set_stage_results(stage_name, stage_results)

            if self.verbose:
                self._log(f"✓ {stage_name} complete")

        context.set_metadata("end_time", datetime.now().isoformat())

        return context

    def dry_run(
        self,
        texts: List[str],
        stages: Optional[List[str]] = None,
    ) -> Dict[str, List[str]]:
        """
        Perform a dry run - build prompts without calling LLM.

        Useful for:
        - Debugging prompts
        - Exporting prompts for review
        - Testing pipeline configuration

        Returns:
            Dict mapping stage_name -> list of prompts (one per task)
        """
        # For dry run, we need to simulate context
        # This is tricky because Stage 2+ depends on Stage 1 results

        # We'll return Stage 1 prompts only (no dependencies)
        execution_order = self.registry.resolve_order(stages)

        prompts: Dict[str, List[str]] = {}
        context = PipelineContext()

        # Only build prompts for first stage (or stages without deps)
        for stage_name in execution_order:
            stage = self.registry.get(stage_name)

            if not stage.dependencies:
                # Can build prompts without prior context
                stage_prompts = []
                for text in texts:
                    prompt = stage.get_prompt_for_export(text, context)
                    if prompt:
                        stage_prompts.append(prompt)

                prompts[stage_name] = stage_prompts
            else:
                prompts[stage_name] = [f"[Requires {stage.dependencies} to run first]"]

        return prompts

    def _log(self, message: str) -> None:
        """Print a log message if verbose mode is on."""
        print(f"[Pipeline] {message}")


class PipelineBuilder:
    """
    Fluent builder for pipeline configuration.

    Usage:
        pipeline = (
            PipelineBuilder()
            .with_content(HandcraftedContentProvider())
            .with_llm(VLLMClient(model="..."))
            .with_stages("default")  # or list of stage classes
            .build()
        )
    """

    def __init__(self):
        self._content = None
        self._schema_factory = None
        self._llm = None
        self._stages = None
        self._verbose = True

    def with_content(self, content) -> "PipelineBuilder":
        """Set the content provider."""
        self._content = content
        return self

    def with_schema_factory(self, factory) -> "PipelineBuilder":
        """Set the schema factory (optional - created from content if not set)."""
        self._schema_factory = factory
        return self

    def with_llm(self, llm: LLMClient) -> "PipelineBuilder":
        """Set the LLM client."""
        self._llm = llm
        return self

    def with_stages(self, stages) -> "PipelineBuilder":
        """
        Set stages to use.

        Args:
            stages: Either "default" for standard 3-stage pipeline,
                    or a list of Stage classes to instantiate,
                    or a StageRegistry instance
        """
        self._stages = stages
        return self

    def verbose(self, enabled: bool = True) -> "PipelineBuilder":
        """Enable/disable verbose output."""
        self._verbose = enabled
        return self

    def build(self) -> PipelineOrchestrator:
        """Build and return the configured orchestrator."""
        # Validate required components
        if self._content is None:
            raise ValueError("Content provider is required. Use .with_content()")

        if self._llm is None:
            raise ValueError("LLM client is required. Use .with_llm()")

        # Create schema factory if not provided
        if self._schema_factory is None:
            from ..schemas import TaxonomySchemaFactory

            self._schema_factory = TaxonomySchemaFactory(self._content)

        # Create registry
        if self._stages is None or self._stages == "default":
            from .registry import create_default_registry

            registry = create_default_registry(self._content, self._schema_factory)
        elif isinstance(self._stages, StageRegistry):
            registry = self._stages
        else:
            # Assume list of stage classes
            registry = StageRegistry()
            for stage_class in self._stages:
                stage = stage_class(self._content, self._schema_factory)
                registry.register(stage)

        return PipelineOrchestrator(
            registry=registry,
            llm=self._llm,
            verbose=self._verbose,
        )
