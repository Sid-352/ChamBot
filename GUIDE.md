# Comprehensive Technical Manual

## 1. Overview
Digital Clone implementation is a process for the extraction, processing, and fine-tuning of massive-scale Discord conversation histories into an autonomous AI persona using the Llama 3.1 8B architecture. This manual details the technical workflows required to overcome API rate-limiting, system memory constraints, and cloud infrastructure limitations.

---

## 2. Hardware Tiers and Optimization

### High-VRAM Systems (RTX 3090 / 4090 / A100)
- **Memory Requirements:** 12GB VRAM or higher.
- **Training Workflow:** Local execution via Unsloth allows for direct GGUF export without cloud intermediate staging.
- **Inference:** Supports high-precision 16-bit or 8-bit GGUF models.

### Low-VRAM Systems 
- **Memory Requirements:** Below 8 GB VRAM; minimum 16GB System RAM for model merging.
- **Training Workflow:** Requires cloud-based Supervised Fine-Tuning (SFT) on Kaggle or Google Colab.
- **Inference Optimization:** Employs 3-bit or 4-bit quantization (Q3_K_M or IQ3_M) to maintain local hardware acceleration.

---

## 3. Phase 1: High-Volume Data Extraction

### Stealth and Anti-Ban Tactics
Discord employs aggressive automated detection for self-botting behavior. Large-scale scrapes (100k+ messages) require human-emulation parameters.
- **Rate Limit Management:** `--respect-rate-limits True` is mandatory.
- **Parallelism Constraints:** High-density channels require single-threading (`--parallel 1`) to prevent connection closure by the remote host.
- **Artificial Latency:** The implementation of artificial delays (e.g., 100ms-500ms) between API requests mimics human reading patterns.
- **Session Isolation:** Discord desktop client must remain completely inactive during extraction. Simultaneous sessions on the same token trigger immediate connection resets.
- **Network Cleanliness:** Using a Mobile Hotspot or VPN for initial account setup avoids linking "burner" accounts to a flagged local IP.

### Distributed Sharding
For datasets exceeding 1 million messages, extraction sharding is necessary. 
- **VPS Deployment:** Deploy multiple VPS instances. Each instance runs a unique, phone-verified alternative account on a distinct cloud IP.
- **Persistence:** Use `screen` or `tmux` on Linux instances to maintain extraction processes across SSH disconnects.

---

## 4. Phase 2: Data Preparation and Repair

### Memory Wall
Standard JSON parsers (e.g., Python's `json.load`) attempt to ingest entire files into RAM. A 4GB file typically expands to 8GB-12GB of RAM during parsing, leading to Out-of-Memory (OOM) crashes.

### Turbo Flattener Stream Pipeline
- **Process:** Streams the raw JSON line-by-line as a text file.
- **Boundary Detection:** Uses Discord's 4-space indentation to identify the start and end of message objects within the `messages` array.
- **Transformation:** Converts nested structures into Newline-Delimited JSON (NDJSON/JSONL). Each line represents one flattened message object including `id`, `timestamp`, `author`, and `content`.
- **Media Preservation:** Empty content fields are coalesced into an `[Attachment]` placeholder to maintain conversational flow.

### Repair Logic
Files that terminate unexpectedly during extraction lack closing JSON syntax (`]}`).
- **Surgical Truncation:** Scans backward from the file end to locate the final complete message object (`},` with `2 indentations`).
- **Structure Completion:** Truncates all trailing corrupted bytes and appends the required closing brackets.

### SQL Context Mapping (DuckDB)
- **Schema Resilience:** Discord JSON contains sparse keys (e.g., `reference` for replies). DuckDB’s `read_json_auto` frequently fails schema inference if the first 2,048 lines lack replies. 
- **The Fix:** Explicitly casting the messages array as `JSON[]` and using null-safe extraction operators (`->>`) prevents binder errors.
- **Deep Windowing:** SQL Window Functions (`LAG` and `LEAD` partitioned by `channel_id`) map each interaction to 3 preceding and 3 subsequent messages from the target's message.
- **Relational Joins:** A self-join on `reply_id` links target's responses to the specific target message, even if located thousands of rows prior.

---

## 5. Phase 3: Dataset Optimization and Pruning

### 10k/70k Ratio Strategy
Total dataset size is pruned to 80,000 interactions to optimize for the GPU training window.
- **Text Priority (70k):** Selects the longest interactions by word count to maximize lore density.
- **Attachment Awareness (10k):** Retains 10,000 random samples where context contains `[Attachment]`. This ensures the persona learns natural reactions to visual media.
- **Recency Weighting:** Multiplies samples from current years to prioritize modern persona. Previous years will have reduced or unary samples.

---

## 6. Phase 4: Cloud Training and Model Creation

### Kaggle: Training Workhorse
Kaggle handles the long training duration of the 80k-sample set.
- **Hyperparameters:** `r=32`, `alpha=64`, `learning_rate=2e-4`, `epochs=1`, `packing=true`.
- **Checkpoints:** Enables step-based saving (e.g., `save_steps=200`) to prevent data loss.

### Google Colab: Export Factory
Kaggle's 20GB disk limit crashes during GGUF conversion (which requires ~40GB for intermediate staging).
- **Workflow:** Upload the Kaggle LoRA checkpoint to Colab. 
- **Merge:** Merges LoRA adapters into the base 16-bit Llama 3.1 model.
- **Quantization:** Exports to GGUF using the `q3/4_k_m` method to accommodate local VRAM.

---

## 7. Phase 5: Local Inference and System Prompt

### LM Studio Configuration
- **Model Preset:** Alpaca
- **Temperature:** 0.65 (balanced between coherence and chaotic energy)
- **GPU Offload:** Max (can be reduced if the system is quite weak)
- **System Prompt:**
> You are <your chosen name\>. You are <traits\> and you remember everyone from the server. Read the Chat Context provided by the user, and respond naturally as yourself.  
>Output Rules:
	> - Use casual formatting: primarily lowercase, minimal punctuation, relaxed grammar.
	> - Keep responses conversational and natural, around 1 to 4 sentences.
	> - Be friendly and approachable. If people are just chatting, engage normally.
	> - Never use standard AI introductory phrases, ethical warnings, or formal essay structures.
	> - Avoid heavy markdown (no bolding, no bulleted lists) so it looks like native chat text.
	> - Read the Chat Context and reply naturally as <name\>.

---

## 8. Continuous Integration
Process employs Cumulative Re-Training. New messages are periodically extracted by the user and merged into the master DuckDB database. The entire combined dataset is then used to fine-tune the base model so the AI maintains a consistent persona while updating its memory of recent events.
