# Classifier Pipeline Test Scripts

This directory contains test scripts for the classifier pipeline.

## Scripts Overview

### 1. `test_pipeline.py` - Full Pipeline Test

Comprehensive test script supporting three modes:

```bash
# Mode 1: Full end-to-end (Schema → YAML → Content Generation → Classification)
python test_pipeline.py \
    --taxonomy /path/to/schema.json \
    --artifacts ./artifacts \
    --export-prompts ./prompts \
    --input-file comments.xlsx \
    --comment-column "comment" \
    --gpu 0 1

# Mode 2: From YAML (skip content generation, use existing artifacts)
python test_pipeline.py \
    --taxonomy /path/to/schema.json \
    --artifacts ./existing_artifacts \
    --skip-generation \
    --input-file comments.xlsx \
    --comment-column "comment"

# Mode 3: From Python prompts (use exported prompt files)
python test_pipeline.py \
    --taxonomy /path/to/schema.json \
    --load-python-prompts ./prompts \
    --input-file comments.xlsx \
    --comment-column "comment"
```

**Key Options:**
- `--taxonomy, -t`: Path to taxonomy schema JSON (required)
- `--artifacts, -a`: Directory for YAML artifacts (default: ./artifacts)
- `--load-python-prompts`: Load from Python prompt files instead of YAML
- `--export-prompts`: Export prompts to Python files
- `--input-file, -i`: Input Excel/CSV file with comments
- `--comment-column`: Column name containing comments (default: "comment")
- `--stages`: Number of stages: 1, 2, or 3 (default: 2)
- `--gpu, -g`: GPU device(s) to use (default: 0)
- `--model`: LLM model name
- `--batch-size`: Batch size for classification
- `--skip-generation`: Skip content generation (use existing artifacts)
- `--skip-classification`: Only generate artifacts/prompts, don't classify
- `--mock-llm`: Use MockLLMClient for testing without GPU

### 2. `test_quick.py` - Quick Development Test

Simple test script for quick development iterations:

```bash
# Quick test with mock LLM (no GPU needed)
python test_quick.py

# Test with specific schema
python test_quick.py --taxonomy /path/to/schema.json

# Test with real comments
python test_quick.py \
    --input-file comments.xlsx \
    --comment-column "comment" \
    --max-comments 10

# Use real LLM (requires GPU)
python test_quick.py --real-llm
```

**Features:**
- Uses MockLLMClient by default for fast testing
- Sample test texts included if no input file
- Concise output showing results

### 3. `test_components.py` - Unit Tests

Tests individual pipeline components in isolation:

```bash
# Run all unit tests
python test_components.py

# Or with pytest
pytest test_components.py -v
```

**Test Coverage:**
- Content providers (Handcrafted, YAML, Composite)
- Schema factory
- Pipeline stages (Category, Element, Attribute)
- Pipeline orchestrator and builder
- Stage registry and dependency resolution
- Result merger
- Mock LLM client
- Prompt exporter
- Artifact scaffolding

## Content Loading Strategy

The test scripts use `CompositeContentProvider` to merge content from multiple sources:

```python
from classifier import HandcraftedContentProvider, YAMLContentProvider
from classifier.content import CompositeContentProvider

content = CompositeContentProvider([
    HandcraftedContentProvider(),  # Priority: battle-tested Stage 1 & 2
    YAMLContentProvider(artifacts_dir),  # Fallback: generated content, Stage 3
])
```

### How Merging Works

| Content Type | Behavior |
|--------------|----------|
| Categories, Elements, Attributes | First provider with non-empty results wins |
| Examples | **Merged** from all providers (deduplicated by text) |
| Rules | **Merged** from all providers (deduplicated) |

### What This Means

- **Stage 1 & 2**: Uses your handcrafted examples/rules (from `provider.py`)
- **Stage 3**: Uses YAML-generated content (handcrafted has none)
- **Gaps**: Any missing content in handcrafted is filled by YAML

### Where Content Appears

| Export | Includes Handcrafted? |
|--------|----------------------|
| YAML Artifacts (`artifacts/`) | ❌ No - scaffolded/generated only |
| Python Prompts (`prompts/`) | ✅ Yes - uses merged CompositeContentProvider |

If you want handcrafted content in YAML files, manually edit them or create a sync utility.

## Default Paths

The scripts use these default paths (update as needed):

```python
DEFAULT_SCHEMA = "/data-fast/data3/clyde/projects/world/documents/schemas/schema_v1.json"
DEFAULT_ARTIFACTS = "./test_artifacts"
DEFAULT_INPUT = "/data-fast/data3/clyde/projects/world/documents/annotator_files/conference_comments_annotated.xlsx"
DEFAULT_COLUMN = "comment"
```

## Workflow Examples

### Example 1: First-time setup with content generation

```bash
# Generate everything from scratch
python test_pipeline.py \
    --taxonomy /path/to/schema.json \
    --artifacts ./my_artifacts \
    --export-prompts ./my_prompts \
    --gpu 0 1 2 3 \
    --model "meta-llama/Llama-3.2-3B-Instruct"
```

### Example 2: Iterate on artifacts without regenerating

```bash
# Edit YAML files manually, then run classification
python test_pipeline.py \
    --taxonomy /path/to/schema.json \
    --artifacts ./my_artifacts \
    --skip-generation \
    --input-file comments.xlsx \
    --stages 3
```

### Example 3: Test with exported Python prompts

```bash
# After exporting prompts, test classification from Python files
python test_pipeline.py \
    --taxonomy /path/to/schema.json \
    --load-python-prompts ./my_prompts \
    --input-file comments.xlsx \
    --mock-llm  # for quick testing
```

### Example 4: Quick sanity check during development

```bash
# Fast test with mock LLM
python test_quick.py --max-comments 3 --stages 2
```

## Output Files

The pipeline saves results to `{artifacts_dir}/../output/`:

- `classification_results_{stages}stage_{timestamp}.csv` - Flat CSV results
- `classification_results_{stages}stage_{timestamp}.json` - Full JSON results
- `classification_stats_{stages}stage.json` - Statistics summary

## Requirements

- Python 3.13+
- classifier package (local)
- pandas (for Excel/CSV reading)
- pydantic

For real LLM inference:
- llm_parallelization package
- CUDA-capable GPU(s)

## Troubleshooting

**"No categories found"**: 
- Check that YAML artifacts have valid `_category.yaml` files
- Ensure schema JSON has the expected structure

**"VLLMClient not available"**:
- Install llm_parallelization package
- Or use `--mock-llm` for testing without GPU

**"Column not found"**:
- Check column names in your input file
- Use `--comment-column "actual_column_name"`
