#!/usr/bin/env python
"""
Unit Tests for Classifier Pipeline Components

Tests individual components in isolation:
- Content providers (Handcrafted, YAML)
- Schema factory
- Pipeline stages
- Result merger
- Prompt exporter

Run with: pytest test_components.py -v
Or directly: python test_components.py
"""

import json
from pathlib import Path
import sys
import tempfile

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


class TestContentProviders:
    """Test content provider implementations."""

    def test_handcrafted_provider_loads_categories(self):
        """HandcraftedContentProvider should load predefined categories."""
        from classifier import HandcraftedContentProvider

        provider = HandcraftedContentProvider()
        categories = provider.get_categories()

        assert len(categories) > 0, "Should have at least one category"
        assert all(hasattr(c, "name") for c in categories), "Categories should have names"
        assert all(hasattr(c, "description") for c in categories), (
            "Categories should have descriptions"
        )

    def test_handcrafted_provider_loads_elements(self):
        """HandcraftedContentProvider should load elements for categories."""
        from classifier import HandcraftedContentProvider

        provider = HandcraftedContentProvider()
        categories = provider.get_categories()

        if categories:
            cat_name = categories[0].name
            elements = provider.get_elements(cat_name)
            # May or may not have elements depending on content
            assert isinstance(elements, list), "Should return a list"

    def test_handcrafted_provider_examples_and_rules(self):
        """HandcraftedContentProvider should return examples and rules."""
        from classifier import HandcraftedContentProvider

        provider = HandcraftedContentProvider()

        stage1_examples = provider.get_examples("stage1")
        stage1_rules = provider.get_rules("stage1")

        assert isinstance(stage1_examples, list), "Examples should be a list"
        assert isinstance(stage1_rules, list), "Rules should be a list"

    def test_yaml_provider_requires_existing_directory(self):
        """YAMLContentProvider should raise error for missing directory."""
        from classifier import YAMLContentProvider
        import pytest

        with tempfile.TemporaryDirectory() as tmpdir:
            nonexistent = Path(tmpdir) / "nonexistent"

            try:
                provider = YAMLContentProvider(str(nonexistent))
                assert False, "Should have raised FileNotFoundError"
            except FileNotFoundError:
                pass  # Expected

    def test_composite_provider_priority(self):
        """CompositeContentProvider should respect priority ordering."""
        from classifier.content import CompositeContentProvider, HandcraftedContentProvider

        provider1 = HandcraftedContentProvider()
        provider2 = HandcraftedContentProvider()

        composite = CompositeContentProvider([provider1, provider2])
        categories = composite.get_categories()

        # Should return from first provider
        assert categories == provider1.get_categories()


class TestSchemaFactory:
    """Test schema factory implementations."""

    def test_taxonomy_schema_factory_creates_stage1_schema(self):
        """TaxonomySchemaFactory should create a valid Stage 1 schema."""
        from classifier import HandcraftedContentProvider, TaxonomySchemaFactory
        from pydantic import BaseModel

        content = HandcraftedContentProvider()
        factory = TaxonomySchemaFactory(content)

        schema = factory.get_stage1_schema()

        assert issubclass(schema, BaseModel), "Should be a Pydantic model"
        assert "categories_present" in schema.model_fields, (
            "Should have categories_present field"
        )

    def test_taxonomy_schema_factory_creates_stage2_schemas(self):
        """TaxonomySchemaFactory should create Stage 2 schemas per category."""
        from classifier import HandcraftedContentProvider, TaxonomySchemaFactory

        content = HandcraftedContentProvider()
        factory = TaxonomySchemaFactory(content)

        categories = content.get_all_category_names()
        if not categories:
            return  # Skip if no categories

        for cat in categories:
            try:
                schema = factory.get_stage2_schema(cat)
                assert "elements" in schema.model_fields, (
                    f"Schema for {cat} should have elements field"
                )
            except ValueError:
                pass  # May fail if no elements for category

    def test_schema_factory_caches_schemas(self):
        """Schema factory should cache generated schemas."""
        from classifier import HandcraftedContentProvider, TaxonomySchemaFactory

        content = HandcraftedContentProvider()
        factory = TaxonomySchemaFactory(content)

        schema1 = factory.get_stage1_schema()
        schema2 = factory.get_stage1_schema()

        assert schema1 is schema2, "Should return cached schema"


class TestPipelineStages:
    """Test individual pipeline stages."""

    def test_category_detection_stage_properties(self):
        """CategoryDetectionStage should have correct properties."""
        from classifier import HandcraftedContentProvider, TaxonomySchemaFactory
        from classifier.stages import CategoryDetectionStage

        content = HandcraftedContentProvider()
        factory = TaxonomySchemaFactory(content)

        stage = CategoryDetectionStage(content, factory)

        assert stage.name == "category_detection"
        assert stage.dependencies == []

    def test_element_extraction_stage_dependencies(self):
        """ElementExtractionStage should depend on category_detection."""
        from classifier import HandcraftedContentProvider, TaxonomySchemaFactory
        from classifier.stages import ElementExtractionStage

        content = HandcraftedContentProvider()
        factory = TaxonomySchemaFactory(content)

        stage = ElementExtractionStage(content, factory)

        assert stage.name == "element_extraction"
        assert "category_detection" in stage.dependencies

    def test_attribute_extraction_stage_dependencies(self):
        """AttributeExtractionStage should depend on element_extraction."""
        from classifier import HandcraftedContentProvider, TaxonomySchemaFactory
        from classifier.stages import AttributeExtractionStage

        content = HandcraftedContentProvider()
        factory = TaxonomySchemaFactory(content)

        stage = AttributeExtractionStage(content, factory)

        assert stage.name == "attribute_extraction"
        assert "element_extraction" in stage.dependencies

    def test_stage_builds_prompt(self):
        """Stages should be able to build prompts."""
        from classifier import HandcraftedContentProvider, TaxonomySchemaFactory
        from classifier.stages import CategoryDetectionStage

        content = HandcraftedContentProvider()
        factory = TaxonomySchemaFactory(content)

        stage = CategoryDetectionStage(content, factory)

        text = "The speaker was excellent!"
        prompt = stage.build_prompt(text)

        assert isinstance(prompt, str), "Prompt should be a string"
        assert len(prompt) > 0, "Prompt should not be empty"
        assert text in prompt, "Prompt should contain the input text"


class TestPipelineOrchestrator:
    """Test pipeline orchestration."""

    def test_pipeline_builder_requires_content(self):
        """PipelineBuilder should require content provider."""
        from classifier import MockLLMClient, PipelineBuilder

        builder = PipelineBuilder()
        builder.with_llm(MockLLMClient())

        try:
            builder.build()
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert "content" in str(e).lower()

    def test_pipeline_builder_requires_llm(self):
        """PipelineBuilder should require LLM client."""
        from classifier import HandcraftedContentProvider, PipelineBuilder

        builder = PipelineBuilder()
        builder.with_content(HandcraftedContentProvider())

        try:
            builder.build()
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert "llm" in str(e).lower()

    def test_pipeline_builder_creates_orchestrator(self):
        """PipelineBuilder should create a PipelineOrchestrator."""
        from classifier import HandcraftedContentProvider, MockLLMClient, PipelineBuilder

        pipeline = (
            PipelineBuilder()
            .with_content(HandcraftedContentProvider())
            .with_llm(MockLLMClient())
            .build()
        )

        from classifier.pipeline import PipelineOrchestrator

        assert isinstance(pipeline, PipelineOrchestrator)

    def test_pipeline_runs_with_mock_llm(self):
        """Pipeline should run with MockLLMClient."""
        from classifier import (
            HandcraftedContentProvider,
            MockLLMClient,
            PipelineBuilder,
        )

        pipeline = (
            PipelineBuilder()
            .with_content(HandcraftedContentProvider())
            .with_llm(MockLLMClient())
            .verbose(False)
            .build()
        )

        texts = ["The speaker was great!"]
        results = pipeline.run(texts, stages=["category_detection"])

        assert len(results) == 1
        assert texts[0] in results


class TestStageRegistry:
    """Test stage registry functionality."""

    def test_registry_registers_stages(self):
        """StageRegistry should register stages."""
        from classifier import HandcraftedContentProvider, TaxonomySchemaFactory
        from classifier.pipeline import StageRegistry
        from classifier.stages import CategoryDetectionStage

        content = HandcraftedContentProvider()
        factory = TaxonomySchemaFactory(content)

        registry = StageRegistry()
        stage = CategoryDetectionStage(content, factory)
        registry.register(stage)

        assert "category_detection" in registry.list_stages()

    def test_registry_prevents_duplicate_registration(self):
        """StageRegistry should prevent duplicate stage names."""
        from classifier import HandcraftedContentProvider, TaxonomySchemaFactory
        from classifier.pipeline import StageRegistry
        from classifier.stages import CategoryDetectionStage

        content = HandcraftedContentProvider()
        factory = TaxonomySchemaFactory(content)

        registry = StageRegistry()
        stage = CategoryDetectionStage(content, factory)
        registry.register(stage)

        try:
            registry.register(stage)
            assert False, "Should have raised ValueError"
        except ValueError:
            pass

    def test_registry_resolves_dependencies(self):
        """StageRegistry should resolve stage dependencies correctly."""
        from classifier import HandcraftedContentProvider, TaxonomySchemaFactory
        from classifier.pipeline import StageRegistry, create_default_registry

        content = HandcraftedContentProvider()
        factory = TaxonomySchemaFactory(content)

        registry = create_default_registry(content, factory)

        # Request only element_extraction, should include category_detection
        order = registry.resolve_order(["element_extraction"])

        assert "category_detection" in order
        assert "element_extraction" in order
        assert order.index("category_detection") < order.index("element_extraction")


class TestResultMerger:
    """Test result merger functionality."""

    def test_merger_merges_empty_context(self):
        """ResultMerger should handle empty context."""
        from classifier.pipeline import PipelineContext, ResultMerger

        context = PipelineContext()
        merger = ResultMerger()

        results = merger.merge(context)

        assert results == {}

    def test_merger_to_flat_records_empty(self):
        """ResultMerger.to_flat_records should handle empty results."""
        from classifier.pipeline import ResultMerger

        merger = ResultMerger()
        records = merger.to_flat_records({})

        assert records == []


class TestMockLLMClient:
    """Test MockLLMClient functionality."""

    def test_mock_client_generates_response(self):
        """MockLLMClient should generate mock responses."""
        from typing import List

        from classifier import MockLLMClient
        from pydantic import BaseModel

        class TestSchema(BaseModel):
            items: List[str]
            count: int

        client = MockLLMClient()
        response = client.generate("test prompt", TestSchema)

        assert response.parsed is not None
        assert isinstance(response.parsed, TestSchema)

    def test_mock_client_tracks_calls(self):
        """MockLLMClient should track call history."""
        from classifier import MockLLMClient
        from pydantic import BaseModel

        class SimpleSchema(BaseModel):
            value: str

        client = MockLLMClient()

        assert client.get_call_count() == 0

        client.generate("prompt 1", SimpleSchema)
        client.generate("prompt 2", SimpleSchema)

        assert client.get_call_count() == 2

    def test_mock_client_batch_generate(self):
        """MockLLMClient should handle batch generation."""
        from classifier import MockLLMClient
        from pydantic import BaseModel

        class SimpleSchema(BaseModel):
            value: str

        client = MockLLMClient()

        prompts = ["prompt 1", "prompt 2", "prompt 3"]
        schemas = [SimpleSchema] * 3

        responses = client.batch_generate(prompts, schemas)

        assert len(responses) == 3
        assert all(r.parsed is not None for r in responses)


class TestPromptExporter:
    """Test prompt exporter functionality."""

    def test_exporter_exports_prompts(self):
        """PromptExporter should export prompt files."""
        from classifier import HandcraftedContentProvider, PromptExporter, TaxonomySchemaFactory

        content = HandcraftedContentProvider()
        factory = TaxonomySchemaFactory(content)
        exporter = PromptExporter(content, factory)

        with tempfile.TemporaryDirectory() as tmpdir:
            result = exporter.export_prompts(tmpdir, verbose=False)

            assert result["files_created"] > 0

            prompts_dir = Path(tmpdir) / "prompts"
            assert prompts_dir.exists()

            # Check stage1 directory
            stage1_dir = prompts_dir / "stage1"
            assert stage1_dir.exists()

    def test_exporter_creates_valid_python(self):
        """PromptExporter should create valid Python files."""
        import ast

        from classifier import HandcraftedContentProvider, PromptExporter, TaxonomySchemaFactory

        content = HandcraftedContentProvider()
        factory = TaxonomySchemaFactory(content)
        exporter = PromptExporter(content, factory)

        with tempfile.TemporaryDirectory() as tmpdir:
            exporter.export_prompts(tmpdir, verbose=False)

            prompts_dir = Path(tmpdir) / "prompts"

            # Check all Python files are valid
            for py_file in prompts_dir.rglob("*.py"):
                try:
                    source = py_file.read_text()
                    ast.parse(source)
                except SyntaxError as e:
                    assert False, f"Invalid Python in {py_file}: {e}"


class TestArtifacts:
    """Test artifact scaffolding and validation."""

    def test_scaffold_creates_structure(self):
        """scaffold_artifacts should create folder structure."""
        from classifier import scaffold_artifacts

        # Create a minimal schema
        schema = {
            "name": "Test",
            "children": [
                {
                    "name": "Category1",
                    "description": "Test category",
                    "children": [
                        {"name": "Element1", "description": "Test element", "children": []}
                    ],
                }
            ],
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            schema_path = Path(tmpdir) / "schema.json"
            artifacts_dir = Path(tmpdir) / "artifacts"

            with open(schema_path, "w") as f:
                json.dump(schema, f)

            result = scaffold_artifacts(str(schema_path), str(artifacts_dir))

            assert artifacts_dir.exists()
            # Check for category folder
            category_folders = list(artifacts_dir.glob("*/"))
            assert len([f for f in category_folders if not f.name.startswith("_")]) > 0


def run_tests():
    """Run all tests and print results."""
    import traceback

    test_classes = [
        TestContentProviders,
        TestSchemaFactory,
        TestPipelineStages,
        TestPipelineOrchestrator,
        TestStageRegistry,
        TestResultMerger,
        TestMockLLMClient,
        TestPromptExporter,
        TestArtifacts,
    ]

    total = 0
    passed = 0
    failed = 0
    errors = []

    print("=" * 60)
    print("RUNNING UNIT TESTS")
    print("=" * 60)

    for test_class in test_classes:
        print(f"\n{test_class.__name__}")
        print("-" * 40)

        instance = test_class()

        for method_name in dir(instance):
            if not method_name.startswith("test_"):
                continue

            total += 1
            method = getattr(instance, method_name)

            try:
                method()
                print(f"  ✓ {method_name}")
                passed += 1
            except AssertionError as e:
                print(f"  ✗ {method_name}: {e}")
                failed += 1
                errors.append((test_class.__name__, method_name, str(e)))
            except Exception as e:
                print(f"  ✗ {method_name}: {type(e).__name__}: {e}")
                failed += 1
                errors.append((test_class.__name__, method_name, traceback.format_exc()))

    print()
    print("=" * 60)
    print(f"RESULTS: {passed}/{total} passed, {failed} failed")
    print("=" * 60)

    if errors:
        print("\nFailed tests:")
        for class_name, method_name, error in errors:
            print(f"\n  {class_name}.{method_name}:")
            for line in error.split("\n")[:5]:
                print(f"    {line}")

    return failed == 0


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
