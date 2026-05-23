# ChamBot Project Structure

## Directory Map
- **.env**: Local configuration file containing the `USER_ID`. This file is private.
- **.env.example**: Template for required environment variables.
- **.gitignore**: Specifies files and directories ignored by version control.
- **/output**: Repository for raw Discord JSON exports. All data retrieval lands here.
- **/scripts**: Directory for Python automation scripts.
- **/notebooks**: Directory containing cloud training and conversion notebooks.
- **/data**: Repository for cleaned .jsonl files.
- **/models**: Repository for local model weights and .gguf files.
- **/logs**: Directory for analysis logs and temporary data.

## Primary Notebooks
- **notebooks/model-creation.ipynb**: Kaggle fine-tuning environment. Handles training and generates zipped LoRA checkpoints.
- **notebooks/convert-to-GGUF.ipynb**: Google Colab conversion environment. Merges weights and exports final 3-bit GGUF files.

## Scripts (in /scripts)

### 1. stream_analyze.py
Scans raw JSON files via RegEx to count total messages linked to the configured `USER_ID`.

### 2. turbo_flattener.py
Converts large Discord JSON files into NDJSON/JSONL using a line-by-line streaming method. Bypasses standard memory constraints.

### 3. dataset_generator.py
Generates the final training dataset via DuckDB. Implements SQL window functions for context mapping and relational joins for reply targets.

### 4. smart_pruner.py
Optimizes the dataset to a specific interaction count. Prioritizes long-form text responses and preserves reactions to visual media context.

### 5. baseline_analyzer.py
Provides frequency statistics for common filler words and attachment context.

## Data Flow
1. Data extraction via DiscordChatExporter into /output.
2. Message analysis via scripts/stream_analyze.py.
3. Format conversion via scripts/turbo_flattener.py.
4. Dataset generation via scripts/dataset_generator.py.
5. Quality pruning via scripts/smart_pruner.py.
6. Model training via notebooks/model-creation.ipynb (Kaggle).
7. GGUF conversion via notebooks/convert-to-GGUF.ipynb (Colab).
8. Local inference via LM Studio.

## Incremental Updates
Update model memory periodically using the Cumulative Re-Training method:
1. Extract new messages using an updated date range.
2. Add the new JSON files to the /output directory.
3. Re-run the preparation scripts to generate a new master dataset.
4. Fine-tune the base Llama 3.1 8B model on the combined dataset.
5. Export the updated .gguf for local use.
