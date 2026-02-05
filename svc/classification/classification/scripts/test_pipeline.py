#!/usr/bin/env python
"""
Full Classification Pipeline Test Script

Tests the classifier pipeline in three modes:
1. Full end-to-end: Schema JSON → YAML artifacts → Content generation → Classification
2. From YAML: Load existing YAML artifacts → Classification (skip generation)
3. From Python prompts: Load exported Python prompts → Classification

Usage:
    # Full pipeline (generate everything)
    python test_pipeline.py \
        --taxonomy /path/to/schema.json \
        --artifacts ./artifacts \
        --export-prompts ./prompts \
        --input-file comments.xlsx \
        --comment-column "comment" \
        --gpu 0 1

    # Skip generation (use existing YAML artifacts)
    python test_pipeline.py \
        --taxonomy /path/to/schema.json \
        --artifacts ./artifacts \
        --skip-generation \
        --input-file comments.xlsx \
        --comment-column "comment"

    # Load from exported Python prompts
    python test_pipeline.py \
        --taxonomy /path/to/schema.json \
        --load-python-prompts ./prompts \
        --input-file comments.xlsx \
        --comment-column "comment"

Workflow:
    schema.json
        → scaffold_artifacts()           # Create folder structure
        → generate_artifact_content()    # LLM fills descriptions/rules/examples
        → YAMLContentProvider            # Load YAML → Python objects
        → TaxonomySchemaFactory          # Build Pydantic schemas
        → PipelineBuilder                # Configure pipeline
        → PipelineOrchestrator.run()     # Run classification
        → ResultMerger.merge()           # Combine stage results
        → PromptExporter.export_prompts()# Export Python prompt files
        → save results
"""

import argparse
from datetime import datetime
import importlib.util
import json
import os
from pathlib import Path
import sys
from typing import Any, Dict, List, Optional, Tuple


def load_comments_from_file(
    filepath: str,
    comment_column: str = "comment",
    sheet_name: str = None,
    max_comments: int = None,
) -> List[str]:
    """Load comments from Excel or CSV file."""
    import pandas as pd

    filepath = Path(filepath)

    if filepath.suffix in (".xlsx", ".xls"):
        df = pd.read_excel(filepath, sheet_name=sheet_name or 0)
    elif filepath.suffix == ".csv":
        df = pd.read_csv(filepath, encoding="utf-8")
    else:
        raise ValueError(f"Unsupported file type: {filepath.suffix}")

    if comment_column not in df.columns:
        available = list(df.columns)
        raise ValueError(f"Column '{comment_column}' not found. Available: {available}")

    comments = df[comment_column].dropna().astype(str).tolist()

    if max_comments:
        comments = comments[:max_comments]

    return comments


def load_taxonomy(taxonomy_path: Path) -> dict:
    """Load taxonomy schema from JSON file."""
    with open(taxonomy_path, "r", encoding="utf-8") as f:
        return json.load(f)


def print_header(title: str, char: str = "=", width: int = 70):
    """Print a formatted header."""
    print(f"\n{char * width}")
    print(title)
    print(char * width)


def print_step(step_num: int, title: str):
    """Print a step header."""
    print_header(f"STEP {step_num}: {title}")


def save_results(
    results: Dict[str, Any],
    flat_records: List[Dict],
    output_dir: Path,
    stages: int,
):
    """Save classification results to files."""
    import pandas as pd

    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Save CSV
    if flat_records:
        df = pd.DataFrame(flat_records)
        csv_path = output_dir / f"classification_results_{stages}stage_{timestamp}.csv"
        df.to_csv(csv_path, index=False, encoding="utf-8-sig")
        print(f"✓ Saved CSV: {csv_path}")

    # Save JSON (full results)
    json_results = []
    for text, result in results.items():
        json_results.append(
            {
                "text": text,
                "categories": [cat.model_dump() for cat in result.categories]
                if hasattr(result, "categories")
                else result,
            }
        )

    json_path = output_dir / f"classification_results_{stages}stage_{timestamp}.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(json_results, f, indent=2, ensure_ascii=False)
    print(f"✓ Saved JSON: {json_path}")

    return csv_path, json_path


def compute_stats(
    results: Dict[str, Any],
    flat_records: List[Dict],
) -> Dict[str, Any]:
    """Compute classification statistics."""
    stats = {
        "total_texts": len(results),
        "total_classifications": len(flat_records),
        "category_distribution": {},
        "element_distribution": {},
        "sentiment_distribution": {},
    }

    for record in flat_records:
        cat = record.get("category")
        elem = record.get("element")
        sentiment = record.get("element_sentiment") or record.get("attribute_sentiment")

        if cat:
            stats["category_distribution"][cat] = stats["category_distribution"].get(cat, 0) + 1
        if elem:
            stats["element_distribution"][elem] = stats["element_distribution"].get(elem, 0) + 1
        if sentiment:
            stats["sentiment_distribution"][sentiment] = (
                stats["sentiment_distribution"].get(sentiment, 0) + 1
            )

    return stats


def print_stats(stats: Dict[str, Any]):
    """Print classification statistics."""
    print(f"\nTotal texts processed: {stats['total_texts']}")
    print(f"Total classifications: {stats['total_classifications']}")

    if stats["category_distribution"]:
        print("\nCategory distribution:")
        for cat, count in sorted(stats["category_distribution"].items(), key=lambda x: -x[1]):
            pct = (
                100 * count / stats["total_classifications"]
                if stats["total_classifications"] > 0
                else 0
            )
            print(f"  {cat}: {count} ({pct:.1f}%)")

    if stats["sentiment_distribution"]:
        print("\nSentiment distribution:")
        for sentiment, count in sorted(
            stats["sentiment_distribution"].items(), key=lambda x: -x[1]
        ):
            pct = (
                100 * count / stats["total_classifications"]
                if stats["total_classifications"] > 0
                else 0
            )
            print(f"  {sentiment}: {count} ({pct:.1f}%)")


# =============================================================================
# Mode-specific pipeline functions
# =============================================================================


def run_full_pipeline(
    taxonomy_path: Path,
    artifacts_dir: Path,
    export_prompts_dir: Optional[Path],
    input_file: Optional[Path],
    comment_column: str,
    sheet_name: Optional[str],
    max_comments: Optional[int],
    stages: int,
    gpu_list: List[int],
    model: str,
    batch_size: int,
    skip_generation: bool,
    skip_attribute_content: bool,
    skip_classification: bool,
    use_mock_llm: bool,
    verbose: bool,
):
    """
    Run the full pipeline from schema to classification.

    Mode: Full end-to-end OR from YAML (with --skip-generation)

    Content Loading Strategy:
    - Uses CompositeContentProvider to merge HandcraftedContentProvider (priority)
      with YAMLContentProvider (fallback for gaps)
    - Handcrafted: Battle-tested Stage 1 & 2 examples/rules
    - YAML: Generated content for Stage 3 and any gaps
    """
    from classifier import (
        HandcraftedContentProvider,
        PipelineBuilder,
        PromptExporter,
        ResultMerger,
        TaxonomySchemaFactory,
        YAMLContentProvider,
        generate_artifact_content,
        scaffold_artifacts,
        validate_artifacts,
    )
    from classifier.content import CompositeContentProvider

    # =========================================================================
    # STEP 1: Scaffold Artifacts
    # =========================================================================
    print_step(1, "SCAFFOLD ARTIFACTS")

    if not artifacts_dir.exists():
        result = scaffold_artifacts(
            schema_path=str(taxonomy_path),
            output_dir=str(artifacts_dir),
            verbose=verbose,
        )
        print("✓ Created artifact structure")
        if isinstance(result, dict):
            print(f"  Files created: {result.get('files_created', 'N/A')}")
    else:
        print(f"✓ Artifacts directory exists: {artifacts_dir}")
        # Validate existing artifacts
        try:
            validation = validate_artifacts(
                artifacts_dir=str(artifacts_dir),
                schema_path=str(taxonomy_path),
                verbose=False,
            )
            if isinstance(validation, dict) and not validation.get("is_valid", True):
                print(f"⚠ Validation issues: {len(validation.get('errors', []))} errors")
                for err in validation.get("errors", [])[:5]:
                    print(f"  - {err}")
        except Exception as e:
            print(f"⚠ Could not validate artifacts: {e}")

    # =========================================================================
    # STEP 2: Generate Content (optional)
    # =========================================================================
    if not skip_generation:
        print_step(2, "GENERATE CONTENT")

        if use_mock_llm:
            print("⚠ Using MockLLMClient - content generation skipped")
            print("  (Use real LLM for actual content generation)")
        else:
            try:
                from llm_parallelization.new_processor import NewProcessor

                processor_config = {
                    "gpu_list": gpu_list,
                    "llm": model,
                    "max_model_len": 8192,
                    "gpu_memory_utilization": 0.9,
                }

                with NewProcessor(**processor_config) as processor:
                    stats = generate_artifact_content(
                        artifacts_dir=str(artifacts_dir),
                        schema_path=str(taxonomy_path),
                        processor=processor,
                        generate_attribute_content=not skip_attribute_content,
                        verbose=verbose,
                    )
                if isinstance(stats, dict):
                    print(
                        f"✓ Generated: {stats.get('descriptions', 0)} descriptions, "
                        f"{stats.get('rules', 0)} rules, {stats.get('examples', 0)} examples"
                    )
            except ImportError:
                print("⚠ llm_parallelization not available - skipping content generation")
            except Exception as e:
                print(f"⚠ Content generation failed: {e}")
    else:
        print_step(2, "SKIP GENERATION (--skip-generation)")

    # =========================================================================
    # STEP 3: Load Content from YAML + Handcrafted
    # =========================================================================
    print_step(3, "LOAD CONTENT (HANDCRAFTED + YAML)")

    # Load YAML content (generated/scaffolded)
    yaml_content = YAMLContentProvider(str(artifacts_dir), verbose=verbose)

    # Load handcrafted content (battle-tested examples/rules)
    handcrafted_content = HandcraftedContentProvider()

    # Combine: Handcrafted has priority, YAML fills gaps
    # - Categories/Elements/Attributes: First provider with content wins
    # - Examples/Rules: MERGED from all providers (deduplicated)
    content = CompositeContentProvider(
        [
            handcrafted_content,  # Priority: battle-tested Stage 1 & 2 content
            yaml_content,  # Fallback: generated content, Stage 3
        ]
    )

    categories = content.get_all_category_names()
    print(f"✓ Loaded {len(categories)} categories")
    for cat in categories:
        elements = content.get_all_element_names(cat)
        print(f"  {cat}: {len(elements)} elements")

    # Show example/rule counts from merged content
    stage1_examples = content.get_examples("stage1")
    stage1_rules = content.get_rules("stage1")
    print(f"✓ Stage 1: {len(stage1_examples)} examples, {len(stage1_rules)} rules")

    # Show breakdown of sources
    handcrafted_s1_examples = handcrafted_content.get_examples("stage1")
    yaml_s1_examples = yaml_content.get_examples("stage1")
    print(f"  (Handcrafted: {len(handcrafted_s1_examples)}, YAML: {len(yaml_s1_examples)})")

    stage2_examples = content.get_examples("stage2")
    handcrafted_s2_examples = handcrafted_content.get_examples("stage2")
    yaml_s2_examples = yaml_content.get_examples("stage2")
    print(f"✓ Stage 2: {len(stage2_examples)} examples")
    print(f"  (Handcrafted: {len(handcrafted_s2_examples)}, YAML: {len(yaml_s2_examples)})")

    # =========================================================================
    # STEP 4: Build Schemas
    # =========================================================================
    print_step(4, "BUILD SCHEMAS")

    schema_factory = TaxonomySchemaFactory(content)

    # Build Stage 1 schema
    stage1_schema = schema_factory.get_stage1_schema()
    print(f"✓ Stage 1 schema: {stage1_schema.__name__}")

    # Build Stage 2 schemas
    stage2_schemas = schema_factory.get_all_stage2_schemas()
    print(f"✓ Stage 2 schemas: {len(stage2_schemas)} categories")

    # Build Stage 3 schemas if needed
    if stages >= 3:
        stage3_schemas = schema_factory.get_all_stage3_schemas()
        total_s3 = len(stage3_schemas)
        print(f"✓ Stage 3 schemas: {total_s3} category/element pairs")

    # =========================================================================
    # STEP 5: Export Prompts (optional)
    # =========================================================================
    if export_prompts_dir:
        print_step(5, "EXPORT PROMPTS")

        exporter = PromptExporter(content, schema_factory)
        result = exporter.export_prompts(str(export_prompts_dir), verbose=verbose)
        print(
            f"✓ Exported {result.get('files_created', 'N/A')} prompt files to {export_prompts_dir}"
        )

    # =========================================================================
    # STEP 6: Build Pipeline
    # =========================================================================
    print_step(6, "BUILD PIPELINE")

    if use_mock_llm:
        from classifier import MockLLMClient

        llm = MockLLMClient()
        print("✓ Using MockLLMClient (for testing)")
    else:
        try:
            from classifier.infrastructure.llm import VLLMClientFactory

            llm = VLLMClientFactory.create(
                gpu_list=gpu_list,
                model=model,
                batch_size=batch_size,
            )
            print(f"✓ Using VLLMClient with {model} on GPU {gpu_list}")
        except ImportError:
            from classifier import MockLLMClient

            llm = MockLLMClient()
            print("⚠ VLLMClient not available, falling back to MockLLMClient")

    pipeline = (
        PipelineBuilder()
        .with_content(content)
        .with_schema_factory(schema_factory)
        .with_llm(llm)
        .verbose(verbose)
        .build()
    )
    print(f"✓ Pipeline ready ({stages}-stage)")

    # =========================================================================
    # STEP 7: Run Classification
    # =========================================================================
    if skip_classification:
        print_step(7, "SKIP CLASSIFICATION (--skip-classification)")
        print("✓ Artifacts and prompts ready!")
        return

    if not input_file:
        print_step(7, "NO INPUT FILE")
        print("✓ Artifacts and prompts ready!")
        print("Run with --input-file to classify comments")
        return

    print_step(7, f"RUN CLASSIFICATION ({stages}-STAGE)")

    # Load comments
    comments = load_comments_from_file(
        str(input_file),
        comment_column=comment_column,
        sheet_name=sheet_name,
        max_comments=max_comments,
    )
    print(f"✓ Loaded {len(comments)} comments from {input_file}")

    # Determine which stages to run
    stage_names = ["category_detection"]
    if stages >= 2:
        stage_names.append("element_extraction")
    if stages >= 3:
        stage_names.append("attribute_extraction")

    print(f"Running stages: {' → '.join(stage_names)}")

    # Run pipeline
    context = pipeline.run_with_context(comments, stages=stage_names)

    # =========================================================================
    # STEP 8: Merge Results
    # =========================================================================
    print_step(8, "MERGE RESULTS")

    merger = ResultMerger()
    final_results = merger.merge(context)
    flat_records = merger.to_flat_records(final_results)

    print(f"✓ Merged {len(final_results)} results")
    print(f"✓ Created {len(flat_records)} flat records")

    # =========================================================================
    # STEP 9: Save Results
    # =========================================================================
    print_step(9, "SAVE RESULTS")

    output_dir = artifacts_dir.parent / "output"
    csv_path, json_path = save_results(final_results, flat_records, output_dir, stages)

    # Compute and save stats
    stats = compute_stats(final_results, flat_records)
    stats_path = output_dir / f"classification_stats_{stages}stage.json"
    with open(stats_path, "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2)
    print(f"✓ Saved stats: {stats_path}")

    # =========================================================================
    # SUMMARY
    # =========================================================================
    print_header("🔥 PIPELINE COMPLETE! 🔥")
    print_stats(stats)
    print(f"\nArtifacts: {artifacts_dir}")
    if export_prompts_dir:
        print(f"Prompts: {export_prompts_dir}")
    print(f"Results: {output_dir}")


def run_from_python_prompts(
    taxonomy_path: Path,
    prompts_dir: Path,
    input_file: Optional[Path],
    comment_column: str,
    sheet_name: Optional[str],
    max_comments: Optional[int],
    stages: int,
    gpu_list: List[int],
    model: str,
    batch_size: int,
    use_mock_llm: bool,
    verbose: bool,
):
    """
    Run classification using pre-exported Python prompt files.

    Mode: From Python prompts (--load-python-prompts)
    """
    print_header("LOADING PROMPTS FROM PYTHON FILES")
    print(f"Prompts directory: {prompts_dir}")

    if not prompts_dir.exists():
        raise FileNotFoundError(f"Prompts directory not found: {prompts_dir}")

    # =========================================================================
    # STEP 1: Load Stage 1 prompt module
    # =========================================================================
    print_step(1, "LOAD STAGE 1 PROMPT")

    stage1_dir = prompts_dir / "stage1"
    if not stage1_dir.exists():
        raise FileNotFoundError(f"Stage 1 directory not found: {stage1_dir}")

    stage1_files = [f for f in stage1_dir.glob("*.py") if f.name != "__init__.py"]
    if not stage1_files:
        raise FileNotFoundError(f"No Stage 1 prompt file found in {stage1_dir}")

    stage1_path = stage1_files[0]
    spec = importlib.util.spec_from_file_location("stage1_module", stage1_path)
    stage1_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(stage1_module)

    # Get categories and prompt builder
    categories = getattr(stage1_module, "CATEGORIES", {})
    build_stage1_prompt = getattr(stage1_module, "build_stage1_prompt", None)

    print(f"✓ Loaded Stage 1 from {stage1_path.name}")
    print(f"  Categories: {list(categories.keys())}")

    # =========================================================================
    # STEP 2: Load Stage 2 prompt modules
    # =========================================================================
    stage2_modules = {}
    if stages >= 2:
        print_step(2, "LOAD STAGE 2 PROMPTS")

        stage2_dir = prompts_dir / "stage2"
        if not stage2_dir.exists():
            raise FileNotFoundError(f"Stage 2 directory not found: {stage2_dir}")

        for category_file in stage2_dir.glob("*.py"):
            if category_file.name == "__init__.py":
                continue

            category_name = category_file.stem
            spec = importlib.util.spec_from_file_location(
                f"stage2_{category_name}", category_file
            )
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            stage2_modules[category_name] = {
                "module": module,
                "elements": getattr(module, "ELEMENTS", {}),
                "build_prompt": getattr(module, "build_stage2_prompt", None),
            }

        print(f"✓ Loaded {len(stage2_modules)} Stage 2 prompts")
        for name, data in stage2_modules.items():
            print(f"  {name}: {len(data['elements'])} elements")

    # =========================================================================
    # STEP 3: Load Stage 3 prompt modules
    # =========================================================================
    stage3_modules = {}
    if stages >= 3:
        print_step(3, "LOAD STAGE 3 PROMPTS")

        stage3_dir = prompts_dir / "stage3"
        if not stage3_dir.exists():
            raise FileNotFoundError(f"Stage 3 directory not found: {stage3_dir}")

        for category_dir in stage3_dir.iterdir():
            if not category_dir.is_dir():
                continue

            category_name = category_dir.name
            stage3_modules[category_name] = {}

            for element_file in category_dir.glob("*.py"):
                if element_file.name == "__init__.py":
                    continue

                element_name = element_file.stem
                spec = importlib.util.spec_from_file_location(
                    f"stage3_{category_name}_{element_name}", element_file
                )
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)

                stage3_modules[category_name][element_name] = {
                    "module": module,
                    "attributes": getattr(module, "ATTRIBUTES", {}),
                    "build_prompt": getattr(module, "build_stage3_prompt", None),
                }

        total_s3 = sum(len(elems) for elems in stage3_modules.values())
        print(f"✓ Loaded {total_s3} Stage 3 prompts")

    # =========================================================================
    # STEP 4: Build Custom Content Provider from Python modules
    # =========================================================================
    print_step(4, "BUILD CONTENT PROVIDER FROM PYTHON MODULES")

    # Create a simple content provider that wraps the loaded Python modules
    from classifier.content.interfaces import (
        AttributeContent,
        CategoryContent,
        ContentProvider,
        ElementContent,
        Example,
        Rule,
    )

    class PythonModuleContentProvider(ContentProvider):
        """Content provider that loads from exported Python prompt modules."""

        def __init__(self, categories, stage2_modules, stage3_modules):
            self._categories = categories
            self._stage2 = stage2_modules
            self._stage3 = stage3_modules

        def get_categories(self):
            return [
                CategoryContent(
                    name=name,
                    description=info.get("description", ""),
                    condensed_description=info.get("description", ""),
                    keywords=[],
                    elements=info.get("elements", []),
                )
                for name, info in self._categories.items()
            ]

        def get_elements(self, category):
            if category not in self._stage2:
                # Try to find by sanitized name
                for key, data in self._stage2.items():
                    if key.lower().replace("_", " ") == category.lower().replace("_", " "):
                        elements_dict = data.get("elements", {})
                        break
                else:
                    return []
            else:
                elements_dict = self._stage2[category].get("elements", {})

            return [
                ElementContent(
                    name=name,
                    category=category,
                    description=info.get("description", ""),
                    condensed_description=info.get("description", ""),
                    keywords=[],
                    attributes=info.get("attributes", []),
                )
                for name, info in elements_dict.items()
            ]

        def get_attributes(self, category, element):
            cat_data = self._stage3.get(category, {})
            elem_data = cat_data.get(element, {})
            attrs_dict = elem_data.get("attributes", {})

            return [
                AttributeContent(
                    name=name,
                    element=element,
                    category=category,
                    description=info.get("description", ""),
                    condensed_description=info.get("description", ""),
                )
                for name, info in attrs_dict.items()
            ]

        def get_examples(self, stage, category=None, element=None):
            # Could load from EXAMPLES in modules if needed
            return []

        def get_rules(self, stage, category=None, element=None):
            # Could load from RULES in modules if needed
            return []

    content = PythonModuleContentProvider(categories, stage2_modules, stage3_modules)
    print("✓ Created content provider from Python modules")

    # =========================================================================
    # STEP 5: Build Pipeline
    # =========================================================================
    print_step(5, "BUILD PIPELINE")

    from classifier import (
        MockLLMClient,
        PipelineBuilder,
        ResultMerger,
        TaxonomySchemaFactory,
    )

    schema_factory = TaxonomySchemaFactory(content)

    if use_mock_llm:
        llm = MockLLMClient()
        print("✓ Using MockLLMClient (for testing)")
    else:
        try:
            from classifier.infrastructure.llm import VLLMClientFactory

            llm = VLLMClientFactory.create(
                gpu_list=gpu_list,
                model=model,
                batch_size=batch_size,
            )
            print(f"✓ Using VLLMClient with {model} on GPU {gpu_list}")
        except ImportError:
            llm = MockLLMClient()
            print("⚠ VLLMClient not available, falling back to MockLLMClient")

    pipeline = (
        PipelineBuilder()
        .with_content(content)
        .with_schema_factory(schema_factory)
        .with_llm(llm)
        .verbose(verbose)
        .build()
    )
    print(f"✓ Pipeline ready ({stages}-stage)")

    # =========================================================================
    # STEP 6: Run Classification
    # =========================================================================
    if not input_file:
        print_step(6, "NO INPUT FILE")
        print("✓ Prompts loaded and pipeline ready!")
        print("Run with --input-file to classify comments")
        return

    print_step(6, f"RUN CLASSIFICATION ({stages}-STAGE)")

    comments = load_comments_from_file(
        str(input_file),
        comment_column=comment_column,
        sheet_name=sheet_name,
        max_comments=max_comments,
    )
    print(f"✓ Loaded {len(comments)} comments")

    stage_names = ["category_detection"]
    if stages >= 2:
        stage_names.append("element_extraction")
    if stages >= 3:
        stage_names.append("attribute_extraction")

    context = pipeline.run_with_context(comments, stages=stage_names)

    # =========================================================================
    # STEP 7: Merge and Save Results
    # =========================================================================
    print_step(7, "MERGE AND SAVE RESULTS")

    merger = ResultMerger()
    final_results = merger.merge(context)
    flat_records = merger.to_flat_records(final_results)

    output_dir = prompts_dir.parent / "output"
    csv_path, json_path = save_results(final_results, flat_records, output_dir, stages)

    stats = compute_stats(final_results, flat_records)

    # =========================================================================
    # SUMMARY
    # =========================================================================
    print_header("🔥 PIPELINE COMPLETE! 🔥")
    print_stats(stats)
    print(f"\nPrompts loaded from: {prompts_dir}")
    print(f"Results: {output_dir}")


# =============================================================================
# Main entry point
# =============================================================================


def main():
    parser = argparse.ArgumentParser(
        description="Full Classification Pipeline Test Script",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Full pipeline (generate everything)
    python test_pipeline.py \\
        --taxonomy schema.json \\
        --artifacts ./artifacts \\
        --export-prompts ./prompts \\
        --input-file comments.xlsx \\
        --comment-column "comment" \\
        --gpu 0 1

    # Skip generation (use existing YAML)
    python test_pipeline.py \\
        --taxonomy schema.json \\
        --artifacts ./artifacts \\
        --skip-generation \\
        --input-file comments.xlsx

    # Load from Python prompts
    python test_pipeline.py \\
        --taxonomy schema.json \\
        --load-python-prompts ./prompts \\
        --input-file comments.xlsx
        """,
    )

    # Required
    parser.add_argument(
        "--taxonomy",
        "-t",
        type=str,
        required=True,
        help="Path to taxonomy schema JSON file",
    )

    # Mode selection
    parser.add_argument(
        "--artifacts",
        "-a",
        type=str,
        default="./artifacts",
        help="Directory for YAML artifacts (default: ./artifacts)",
    )
    parser.add_argument(
        "--load-python-prompts",
        type=str,
        help="Load prompts from existing Python files (skips YAML workflow)",
    )

    # Export
    parser.add_argument(
        "--export-prompts",
        type=str,
        help="Directory to export Python prompt files",
    )

    # Input
    parser.add_argument(
        "--input-file",
        "-i",
        type=str,
        help="Input file with comments (Excel or CSV)",
    )
    parser.add_argument(
        "--comment-column",
        type=str,
        default="comment",
        help="Column name containing comments (default: comment)",
    )
    parser.add_argument(
        "--sheet-name",
        type=str,
        help="Sheet name for Excel files",
    )
    parser.add_argument(
        "--max-comments",
        type=int,
        help="Maximum comments to process",
    )

    # Pipeline options
    parser.add_argument(
        "--stages",
        type=int,
        choices=[1, 2, 3],
        default=2,
        help="Number of classification stages (default: 2)",
    )

    # GPU and model
    parser.add_argument(
        "--gpu",
        "-g",
        type=int,
        nargs="+",
        default=[0],
        help="GPU device(s) to use (default: 0)",
    )
    parser.add_argument(
        "--model",
        type=str,
        default="meta-llama/Llama-3.2-3B-Instruct",
        help="Model to use for LLM processing",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=25,
        help="Batch size for classification (default: 25)",
    )

    # Skip options
    parser.add_argument(
        "--skip-generation",
        action="store_true",
        help="Skip content generation (use existing artifacts)",
    )
    parser.add_argument(
        "--skip-attribute-content",
        action="store_true",
        help="Skip generating content for attribute-level YAML files",
    )
    parser.add_argument(
        "--skip-classification",
        action="store_true",
        help="Skip classification (artifacts and prompts only)",
    )

    # Testing
    parser.add_argument(
        "--mock-llm",
        action="store_true",
        help="Use MockLLMClient instead of real LLM (for testing)",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        default=True,
        help="Verbose output (default: True)",
    )
    parser.add_argument(
        "--quiet",
        "-q",
        action="store_true",
        help="Suppress verbose output",
    )

    args = parser.parse_args()

    # Handle verbose flag
    verbose = args.verbose and not args.quiet

    # Validate paths
    taxonomy_path = Path(args.taxonomy)
    if not taxonomy_path.exists():
        print(f"ERROR: Taxonomy file not found: {taxonomy_path}")
        sys.exit(1)

    # Print configuration
    print_header("CLASSIFICATION PIPELINE TEST")
    print(f"Taxonomy: {taxonomy_path}")
    print(f"Stages: {args.stages}")
    print(f"GPU(s): {args.gpu}")
    print(f"Model: {args.model}")

    if args.load_python_prompts:
        print("Mode: LOAD FROM PYTHON PROMPTS")
        print(f"Prompts: {args.load_python_prompts}")
    else:
        print("Mode: YAML ARTIFACTS")
        print(f"Artifacts: {args.artifacts}")
        if args.skip_generation:
            print("  (skipping generation)")

    if args.input_file:
        print(f"Input: {args.input_file}")
        print(f"Column: {args.comment_column}")

    # Dispatch to appropriate mode
    try:
        if args.load_python_prompts:
            run_from_python_prompts(
                taxonomy_path=taxonomy_path,
                prompts_dir=Path(args.load_python_prompts),
                input_file=Path(args.input_file) if args.input_file else None,
                comment_column=args.comment_column,
                sheet_name=args.sheet_name,
                max_comments=args.max_comments,
                stages=args.stages,
                gpu_list=args.gpu,
                model=args.model,
                batch_size=args.batch_size,
                use_mock_llm=args.mock_llm,
                verbose=verbose,
            )
        else:
            run_full_pipeline(
                taxonomy_path=taxonomy_path,
                artifacts_dir=Path(args.artifacts),
                export_prompts_dir=Path(args.export_prompts) if args.export_prompts else None,
                input_file=Path(args.input_file) if args.input_file else None,
                comment_column=args.comment_column,
                sheet_name=args.sheet_name,
                max_comments=args.max_comments,
                stages=args.stages,
                gpu_list=args.gpu,
                model=args.model,
                batch_size=args.batch_size,
                skip_generation=args.skip_generation,
                skip_attribute_content=args.skip_attribute_content,
                skip_classification=args.skip_classification,
                use_mock_llm=args.mock_llm,
                verbose=verbose,
            )
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nERROR: {e}")
        if verbose:
            import traceback

            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
