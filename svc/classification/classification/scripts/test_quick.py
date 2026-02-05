#!/usr/bin/env python
"""
Quick Test Script for Classifier Pipeline

Simple test script for quick development iterations and sanity checks.
Uses MockLLMClient by default for fast testing without GPU.

Usage:
    # Quick test with mock LLM
    python test_quick.py

    # Test with specific schema
    python test_quick.py --taxonomy /path/to/schema.json

    # Test from existing YAML artifacts
    python test_quick.py --artifacts /path/to/artifacts

    # Test with real comments
    python test_quick.py --input-file comments.xlsx --comment-column "comment"
"""

import argparse
import json
from pathlib import Path
import sys

# Default paths - update these for your environment
DEFAULT_SCHEMA = "/data-fast/data3/clyde/projects/world/documents/schemas/schema_v1.json"
DEFAULT_ARTIFACTS = "./test_artifacts"
DEFAULT_INPUT = "/data-fast/data3/clyde/projects/world/documents/annotator_files/conference_comments_annotated.xlsx"
DEFAULT_COLUMN = "comment"


def run_quick_test(
    taxonomy_path: str = None,
    artifacts_dir: str = None,
    input_file: str = None,
    comment_column: str = DEFAULT_COLUMN,
    max_comments: int = 5,
    stages: int = 2,
    use_mock: bool = True,
    verbose: bool = True,
):
    """Run a quick test of the pipeline."""

    # Use defaults if not provided
    taxonomy_path = taxonomy_path or DEFAULT_SCHEMA
    artifacts_dir = artifacts_dir or DEFAULT_ARTIFACTS

    print("=" * 60)
    print("QUICK TEST - Classifier Pipeline")
    print("=" * 60)
    print(f"Schema: {taxonomy_path}")
    print(f"Artifacts: {artifacts_dir}")
    print(f"Stages: {stages}")
    print(f"Mock LLM: {use_mock}")
    print()

    # Import classifier components
    from classifier import (
        HandcraftedContentProvider,
        MockLLMClient,
        PipelineBuilder,
        PromptExporter,
        ResultMerger,
        TaxonomySchemaFactory,
        YAMLContentProvider,
        scaffold_artifacts,
    )
    from classifier.content import CompositeContentProvider

    # =========================================================================
    # Step 1: Scaffold artifacts if needed
    # =========================================================================
    print("[1/6] Scaffolding artifacts...")

    artifacts_path = Path(artifacts_dir)
    if not artifacts_path.exists():
        if not Path(taxonomy_path).exists():
            print(f"ERROR: Schema file not found: {taxonomy_path}")
            sys.exit(1)

        scaffold_artifacts(taxonomy_path, str(artifacts_path))
        print(f"  ✓ Created artifacts at {artifacts_path}")
    else:
        print(f"  ✓ Using existing artifacts at {artifacts_path}")

    # =========================================================================
    # Step 2: Load content (Handcrafted + YAML)
    # =========================================================================
    print("[2/6] Loading content (Handcrafted + YAML)...")

    try:
        # Load both content sources
        yaml_content = YAMLContentProvider(str(artifacts_path), verbose=False)
        handcrafted_content = HandcraftedContentProvider()

        # Combine: Handcrafted has priority, YAML fills gaps
        content = CompositeContentProvider(
            [
                handcrafted_content,  # Priority: battle-tested
                yaml_content,  # Fallback: generated
            ]
        )

        categories = content.get_all_category_names()
        print(f"  ✓ Loaded {len(categories)} categories:")
        for cat in categories[:5]:  # Show first 5
            elements = content.get_all_element_names(cat)
            print(f"      - {cat}: {len(elements)} elements")
        if len(categories) > 5:
            print(f"      ... and {len(categories) - 5} more")

        # Show merged example counts
        s1_examples = content.get_examples("stage1")
        s2_examples = content.get_examples("stage2")
        print(f"  ✓ Examples: {len(s1_examples)} Stage 1, {len(s2_examples)} Stage 2")

    except Exception as e:
        print(f"  ✗ Failed to load content: {e}")
        print("  Tip: Make sure artifacts have been generated with content")
        sys.exit(1)

    # =========================================================================
    # Step 3: Build schemas
    # =========================================================================
    print("[3/6] Building schemas...")

    schema_factory = TaxonomySchemaFactory(content)
    stage1_schema = schema_factory.get_stage1_schema()
    stage2_schemas = schema_factory.get_all_stage2_schemas()

    print("  ✓ Stage 1 schema ready")
    print(f"  ✓ Stage 2 schemas: {len(stage2_schemas)} categories")

    if stages >= 3:
        stage3_schemas = schema_factory.get_all_stage3_schemas()
        print(f"  ✓ Stage 3 schemas: {len(stage3_schemas)} pairs")

    # =========================================================================
    # Step 4: Build pipeline
    # =========================================================================
    print("[4/6] Building pipeline...")

    if use_mock:
        llm = MockLLMClient()
        print("  ✓ Using MockLLMClient")
    else:
        try:
            from classifier.infrastructure.llm import VLLMClientFactory

            llm = VLLMClientFactory.create(gpu_list=[0])
            print("  ✓ Using VLLMClient")
        except ImportError:
            llm = MockLLMClient()
            print("  ⚠ VLLMClient not available, using MockLLMClient")

    pipeline = (
        PipelineBuilder()
        .with_content(content)
        .with_schema_factory(schema_factory)
        .with_llm(llm)
        .verbose(verbose)
        .build()
    )
    print("  ✓ Pipeline ready")

    # =========================================================================
    # Step 5: Run classification
    # =========================================================================
    print("[5/6] Running classification...")

    # Get test texts
    if input_file and Path(input_file).exists():
        import pandas as pd

        df = pd.read_excel(input_file)
        if comment_column in df.columns:
            comments = df[comment_column].dropna().astype(str).tolist()[:max_comments]
            print(f"  Loaded {len(comments)} comments from {input_file}")
        else:
            print(f"  ⚠ Column '{comment_column}' not found, using sample texts")
            comments = None
    else:
        comments = None

    if not comments:
        # Sample test texts
        comments = [
            "The keynote speaker was absolutely brilliant! Her insights on AI were groundbreaking.",
            "WiFi kept dropping during the sessions and the venue was too cold.",
            "I loved the networking dinner! Met so many interesting people in my field.",
            "The workshop materials were outdated, and the presenter seemed unprepared.",
            "Overall, this was the best conference I've attended in years. Totally worth the price.",
        ][:max_comments]
        print(f"  Using {len(comments)} sample texts")

    # Determine stages to run
    stage_names = ["category_detection"]
    if stages >= 2:
        stage_names.append("element_extraction")
    if stages >= 3:
        stage_names.append("attribute_extraction")

    print(f"  Running: {' → '.join(stage_names)}")

    context = pipeline.run_with_context(comments, stages=stage_names)
    print("  ✓ Classification complete")

    # =========================================================================
    # Step 6: Merge and display results
    # =========================================================================
    print("[6/6] Merging results...")

    merger = ResultMerger()
    final_results = merger.merge(context)
    flat_records = merger.to_flat_records(final_results)

    print(f"  ✓ Merged {len(final_results)} results")
    print(f"  ✓ Created {len(flat_records)} flat records")

    # =========================================================================
    # Display results
    # =========================================================================
    print()
    print("=" * 60)
    print("RESULTS")
    print("=" * 60)

    for text, result in final_results.items():
        print(f"\n📝 {text[:60]}...")
        if hasattr(result, "categories"):
            for cat in result.categories:
                print(f"  📁 {cat.name}")
                if hasattr(cat, "elements"):
                    for elem in cat.elements:
                        sentiment = (
                            elem.sentiment.value
                            if hasattr(elem.sentiment, "value")
                            else elem.sentiment
                        )
                        print(f"      → {elem.name} ({sentiment})")
                        if hasattr(elem, "attributes") and elem.attributes:
                            for attr in elem.attributes:
                                attr_sentiment = (
                                    attr.sentiment.value
                                    if hasattr(attr.sentiment, "value")
                                    else attr.sentiment
                                )
                                print(f"          • {attr.name} ({attr_sentiment})")

    # =========================================================================
    # Summary statistics
    # =========================================================================
    print()
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)

    # Count categories
    cat_counts = {}
    sentiment_counts = {}
    for record in flat_records:
        cat = record.get("category")
        if cat:
            cat_counts[cat] = cat_counts.get(cat, 0) + 1

        sentiment = record.get("element_sentiment") or record.get("attribute_sentiment")
        if sentiment:
            sentiment_counts[sentiment] = sentiment_counts.get(sentiment, 0) + 1

    print(f"Total texts: {len(final_results)}")
    print(f"Total classifications: {len(flat_records)}")

    if cat_counts:
        print("\nCategories:")
        for cat, count in sorted(cat_counts.items(), key=lambda x: -x[1]):
            print(f"  {cat}: {count}")

    if sentiment_counts:
        print("\nSentiments:")
        for sentiment, count in sorted(sentiment_counts.items(), key=lambda x: -x[1]):
            print(f"  {sentiment}: {count}")

    print()
    print("=" * 60)
    print("✅ Quick test completed successfully!")
    print("=" * 60)

    return final_results, flat_records


def main():
    parser = argparse.ArgumentParser(description="Quick test script for classifier pipeline")

    parser.add_argument(
        "--taxonomy",
        "-t",
        type=str,
        default=DEFAULT_SCHEMA,
        help=f"Path to taxonomy schema JSON (default: {DEFAULT_SCHEMA})",
    )
    parser.add_argument(
        "--artifacts",
        "-a",
        type=str,
        default=DEFAULT_ARTIFACTS,
        help=f"Directory for YAML artifacts (default: {DEFAULT_ARTIFACTS})",
    )
    parser.add_argument(
        "--input-file",
        "-i",
        type=str,
        default=None,
        help="Input file with comments (optional)",
    )
    parser.add_argument(
        "--comment-column",
        type=str,
        default=DEFAULT_COLUMN,
        help=f"Column name containing comments (default: {DEFAULT_COLUMN})",
    )
    parser.add_argument(
        "--max-comments",
        type=int,
        default=5,
        help="Maximum comments to process (default: 5)",
    )
    parser.add_argument(
        "--stages",
        type=int,
        choices=[1, 2, 3],
        default=2,
        help="Number of classification stages (default: 2)",
    )
    parser.add_argument(
        "--real-llm",
        action="store_true",
        help="Use real LLM instead of MockLLMClient",
    )
    parser.add_argument(
        "--quiet",
        "-q",
        action="store_true",
        help="Suppress verbose pipeline output",
    )

    args = parser.parse_args()

    run_quick_test(
        taxonomy_path=args.taxonomy,
        artifacts_dir=args.artifacts,
        input_file=args.input_file,
        comment_column=args.comment_column,
        max_comments=args.max_comments,
        stages=args.stages,
        use_mock=not args.real_llm,
        verbose=not args.quiet,
    )


if __name__ == "__main__":
    main()
