from classifier import (
    MockLLMClient,  # or VLLMClient with your processor
    PipelineBuilder,
    PromptExporter,
    ResultMerger,
    TaxonomySchemaFactory,
    YAMLContentProvider,
    scaffold_artifacts,
)

scaffold_artifacts(
    "/data-fast/data3/clyde/projects/world/documents/schemas/schema_v1.json", "./artifacts_test"
)
artifacts_path = "/data-fast/data3/clyde/projects/world/documents/output_files/new_tests_yaml"
content = YAMLContentProvider(artifacts_path, verbose=True)

# Check what was loaded
print(f"Categories: {content.get_all_category_names()}")
for cat in content.get_all_category_names():
    elements = content.get_all_element_names(cat)
    print(f"  {cat}: {elements}")

# 2. Get examples and rules
stage1_examples = content.get_examples("stage1")
print(f"\nStage 1 examples: {len(stage1_examples)}")

stage2_examples = content.get_examples("stage2", category="People")
print(f"Stage 2 examples for People: {len(stage2_examples)}")


# 1. Load content from your existing artifacts
artifacts_path = "/data-fast/data3/clyde/projects/world/documents/output_files/new_tests_yaml"
content = YAMLContentProvider(artifacts_path, verbose=True)

# Check what was loaded
print(f"Categories: {content.get_all_category_names()}")
for cat in content.get_all_category_names():
    elements = content.get_all_element_names(cat)
    print(f"  {cat}: {elements}")

# 2. Get examples and rules
stage1_examples = content.get_examples("stage1")
print(f"\nStage 1 examples: {len(stage1_examples)}")

stage2_examples = content.get_examples("stage2", category="People")
print(f"Stage 2 examples for People: {len(stage2_examples)}")

# 3. Build pipeline
schema_factory = TaxonomySchemaFactory(content)
llm = MockLLMClient()  # Replace with VLLMClient(processor) for real inference

pipeline = PipelineBuilder().with_content(content).with_llm(llm).build()

# 4. Run classification
texts = ["The speaker was amazing and very knowledgeable!", "WiFi was terrible."]
# context = pipeline.run(texts, stages=["category_detection", "element_extraction"])
context = pipeline.run_with_context(texts, stages=["category_detection", "element_extraction"])

# 5. Merge results
merger = ResultMerger()
final_results = merger.merge(context)

for text, result in final_results.items():
    print(f"\n{text[:50]}...")
    for cat in result.categories:
        print(f"  → {cat.name}")
        for elem in cat.elements:
            print(f"      → {elem.name} ({elem.sentiment})")

# 6. (Optional) Export prompts for review
exporter = PromptExporter(content, schema_factory)
exporter.export_prompts("./exported_prompts")
__import__("ipdb").set_trace()
