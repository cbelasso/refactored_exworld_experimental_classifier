#!/usr/bin/env python3
"""
Example Usage of the Refactored Classifier

This script demonstrates:
1. Setting up the pipeline with handcrafted content
2. Running classification on sample texts
3. Exporting prompts for review
4. Inspecting results
"""

import json
from pathlib import Path

from lib.classifier.src.classifier import (
    # Content
    HandcraftedContentProvider,
    # LLM
    MockLLMClient,
    # Pipeline
    PipelineBuilder,
    # Export
    PromptExporter,
    # Schemas
    TaxonomySchemaFactory,
)


def main():
    """Run example classification pipeline."""

    print("=" * 60)
    print("Refactored Classifier - Example Usage")
    print("=" * 60)

    # 1. Setup content provider
    print("\n1. Setting up content provider...")
    content = HandcraftedContentProvider()

    # Show what categories are available
    categories = content.get_all_category_names()
    print(f"   Available categories: {categories}")

    # Show elements for first category
    first_cat = categories[0]
    elements = content.get_all_element_names(first_cat)
    print(f"   Elements in '{first_cat}': {elements}")

    # 2. Create schema factory
    print("\n2. Creating schema factory...")
    schema_factory = TaxonomySchemaFactory(content)

    # Show that schemas are dynamically built
    Stage1Schema = schema_factory.get_stage1_schema()
    print(f"   Stage 1 schema: {Stage1Schema.__name__}")
    print(f"   Schema fields: {list(Stage1Schema.model_fields.keys())}")

    # 3. Setup LLM client (mock for demo)
    print("\n3. Setting up LLM client (mock)...")

    # Configure mock to return reasonable responses
    mock_responses = {
        "speakers were excellent": {
            "categories_present": ["People", "Learning & Content Delivery"],
            "reasoning": "Discusses speakers (People) and their delivery quality",
        },
        "WiFi was terrible": {
            "categories_present": ["Event Logistics"],
            "reasoning": "Discusses technical infrastructure issues",
        },
        "great networking": {
            "categories_present": ["Networking & Social"],
            "reasoning": "Discusses networking opportunities",
        },
    }

    llm = MockLLMClient(responses=mock_responses)

    # 4. Build the pipeline
    print("\n4. Building pipeline...")
    pipeline = PipelineBuilder().with_content(content).with_llm(llm).verbose(True).build()

    # 5. Sample texts to classify
    sample_texts = [
        "The speakers were excellent and really knew their stuff!",
        "WiFi was terrible throughout the conference.",
        "Great networking opportunities at the evening reception.",
    ]

    print("\n5. Running classification pipeline...")
    print("-" * 40)

    # Run just Stage 1 first
    results = pipeline.run(
        texts=sample_texts,
        stages=["category_detection"],  # Just Stage 1
    )

    print("\n6. Results:")
    print("-" * 40)
    for text, result in results.items():
        print(f'\nText: "{text[:50]}..."')
        if "category_detection" in result:
            cat_result = result["category_detection"]
            categories = getattr(cat_result, "categories_present", [])
            print(f"  Categories: {categories}")

    # 7. Export prompts for review
    print("\n7. Exporting prompts...")
    exporter = PromptExporter(content, schema_factory)

    export_dir = Path("./exported_prompts_example")
    exported = exporter.export_hierarchical(str(export_dir))
    print(f"   Exported {len(exported)} files to {export_dir}")

    # Show sample prompt
    print("\n8. Sample Stage 1 prompt:")
    print("-" * 40)
    stage1_prompt = content.get_examples("stage1")[0]  # First example
    prompt = pipeline.registry.get("category_detection").build_prompt(
        "Sample feedback about the conference."
    )
    # Show first 500 chars
    print(prompt[:500] + "...\n")

    # 9. Show LLM call count
    print(f"9. Total LLM calls made: {llm.get_call_count()}")

    print("\n" + "=" * 60)
    print("Example complete!")
    print("=" * 60)


def demo_stage_by_stage():
    """
    Demonstrate running stages individually with inspection.
    """
    print("\n--- Stage-by-Stage Demo ---\n")

    content = HandcraftedContentProvider()
    schema_factory = TaxonomySchemaFactory(content)
    llm = MockLLMClient()

    # Create individual stages
    from lib.classifier.src.classifier import (
        CategoryDetectionStage,
        ElementExtractionStage,
    )

    stage1 = CategoryDetectionStage(content, schema_factory)
    stage2 = ElementExtractionStage(content, schema_factory)

    print(f"Stage 1: {stage1.name}")
    print(f"  Dependencies: {stage1.dependencies}")

    print(f"\nStage 2: {stage2.name}")
    print(f"  Dependencies: {stage2.dependencies}")

    # Build a prompt and inspect it
    sample_text = "The keynote speaker was inspiring!"
    prompt = stage1.build_prompt(sample_text)

    print(f"\nPrompt length: {len(prompt)} characters")
    print(f"First 200 chars:\n{prompt[:200]}...")


def demo_content_modification():
    """
    Demonstrate how easy it is to modify content.
    """
    print("\n--- Content Modification Demo ---\n")

    # The handcrafted content is in Python dicts - easy to modify!
    from lib.classifier.src.classifier.content.handcrafted.provider import (
        CATEGORIES,
        STAGE1_EXAMPLES,
    )

    print("Current categories:")
    for name in CATEGORIES.keys():
        print(f"  - {name}")

    print(f"\nNumber of Stage 1 examples: {len(STAGE1_EXAMPLES)}")

    print("\nTo add a new example, edit:")
    print("  refactored_classifier/content/handcrafted/provider.py")
    print("\nAdd to STAGE1_EXAMPLES:")
    print("""  {
      "text": "Your new example text",
      "output": {
          "categories_present": ["Category1", "Category2"],
          "reasoning": "Explanation"
      }
  }""")


if __name__ == "__main__":
    main()

    # Uncomment to run additional demos:
    # demo_stage_by_stage()
    # demo_content_modification()
