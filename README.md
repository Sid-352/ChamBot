# ChamBot

## Objective
The project provides a comprehensive pipeline for extracting, processing, and fine-tuning large-scale Discord chat histories into an autonomous AI persona using the Llama 3.1 8B architecture.

## Architecture
The system consists of six primary phases:
1. Data Extraction: **[DiscordChatExporter](https://github.com/Tyrrrz/DiscordChatExporter)** (needs to be downloaded yourself) retrieves raw message data from target channels.
2. Data Processing: Python scripts parse raw JSON files into Newline-Delimited JSON (NDJSON/JSONL).
3. Context Mapping: DuckDB executes relational joins to map user messages to preceding context, subsequent context, and explicit reply targets.
4. Heuristic Pruning: The pipeline reduces the dataset to 80,000 high-quality interactions, preserving visual media context while prioritizing detailed text responses.
5. Cloud Fine-Tuning: **notebooks/model-creation.ipynb** (Kaggle) handles LoRA training and generates zipped checkpoints.
6. Model Conversion: **notebooks/convert-to-GGUF.ipynb** (Google Colab) merges weights and exports the final GGUF file.

## Configuration
The system requires a **.env** file in the root directory containing the `USER_ID`. Refer to **.env.example** for the template.

## Execution
The final output is a GGUF file. One can execute this file locally via LM Studio using the Alpaca prompt format. A specific system prompt enforces the behavioural constraints and suppresses standard AI assistant patterns.

## Documentation
Refer to **[GUIDE.MD](https://github.com/Sid-352/ChamBot/blob/main/GUIDE.md)** for technical implementation details, hardware specifications, and cloud infrastructure strategies. Refer to **[PROJECT_MAP.md](https://github.com/Sid-352/ChamBot/blob/main/PROJECT_MAP.md)** for directory structure and script functions.
