import json
import os
import random

"""
Smart Pruner: Targeted 80k Selection
-----------------------------------
This script executes the specific 10k/70k split requested.

Logic:
1. Divide the dataset into two pools: 'With Attachment' and 'Text Only'.
2. Selection Criteria:
   - For 'Text Only': Prioritize the longest responses (top 70,000 by word count) 
     to ensure the model learns complex vocabulary and detailed sentence structures.
   - For 'With Attachment': Take a random sample of 10,000 to maintain the 
     natural variety of how the persona reacts to media.
3. Combine and shuffle the 80k to ensure even training across years and topics.

Paths are calculated relative to this script's location.
"""

# Calculate the project root relative to this script (in /scripts)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

INPUT_FILE = os.path.join(BASE_DIR, "data", "final_dataset.jsonl")
OUTPUT_FILE = os.path.join(BASE_DIR, "data", "dataset_80k.jsonl")

def smart_prune():
    if not os.path.exists(INPUT_FILE):
        print(f"Error: {INPUT_FILE} not found.")
        return

    print("Loading dataset for surgical pruning...")
    attachment_pool = []
    text_pool = []

    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            try:
                item = json.loads(line)
                if "[Attachment]" in item.get("instruction", ""):
                    attachment_pool.append(item)
                else:
                    text_pool.append(item)
            except:
                continue

    print(f"Pool Sizes:")
    print(f" - Attachment Pool: {len(attachment_pool):,} samples")
    print(f" - Text-Only Pool:  {len(text_pool):,} samples")

    # 1. Select the "Best" 70k Text Messages
    print("\nSelecting top 70,000 text messages by length...")
    text_pool.sort(key=lambda x: len(x["output"].split()), reverse=True)
    selected_text = text_pool[:70000]

    # 2. Select 10,000 Image Reactions
    print("Selecting 10,000 random image reactions...")
    random.seed(3407)
    selected_attachment = random.sample(attachment_pool, min(10000, len(attachment_pool)))

    # 3. Combine and Shuffle
    final_dataset = selected_text + selected_attachment
    random.shuffle(final_dataset)

    print(f"\nFinal Dataset Composition:")
    print(f" - Total Samples: {len(final_dataset):,}")
    
    # 4. Save to disk
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        for item in final_dataset:
            f.write(json.dumps(item) + '\n')

    print(f"\nSUCCESS! Polished 80k dataset saved to: {OUTPUT_FILE}")
    print("Next Move: Upload to cloud training environment.")

if __name__ == "__main__":
    smart_prune()
