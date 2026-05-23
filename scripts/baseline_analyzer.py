import json
import os
from collections import Counter

"""
Baseline Analyzer: Data Quality Assessment
------------------------------------------
This script calculates frequency statistics for common filler words 
and attachment context. It helps in calibrating the pruning strategy.

Paths are calculated relative to this script's location.
"""

# Calculate the project root relative to this script (in /scripts)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DATASET_FILE = os.path.join(BASE_DIR, "data", "final_dataset.jsonl")

# Target words for frequency analysis
TARGET_WORDS = ["lol", "ok", "sure", "k", "eh", "meh", "sob", "nah"]

def analyze_baseline():
    if not os.path.exists(DATASET_FILE):
        print(f"Error: {DATASET_FILE} not found.")
        return

    print(f"Starting baseline analysis on: {os.path.basename(DATASET_FILE)}...")

    stats = {word: 0 for word in TARGET_WORDS}
    attachment_in_context = 0
    attachment_in_output = 0
    total_lines = 0

    with open(DATASET_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            total_lines += 1
            try:
                data = json.loads(line)
            except:
                continue
                
            inst = data.get("instruction", "")
            out = data.get("output", "").strip().lower()

            # Count exact matches for target filler words
            if out in stats:
                stats[out] += 1
            
            # Count [Attachment] occurrences
            if "[Attachment]" in inst:
                attachment_in_context += 1
            if "[Attachment]" in out:
                attachment_in_output += 1

    print("\n" + "="*30)
    print(f"  BASELINE DATASET STATS")
    print("="*30)
    print(f"Total Weighted Lines: {total_lines:,}\n")

    print("--- FILLER WORD COUNTS (Exact Output Match) ---")
    for word, count in stats.items():
        percentage = (count / total_lines) * 100
        print(f" '{word}': {count:,} ({percentage:.2f}%)")

    print("\n--- ATTACHMENT STATS ---")
    ctx_perc = (attachment_in_context / total_lines) * 100
    out_perc = (attachment_in_output / total_lines) * 100
    print(f" [Attachment] in Context: {attachment_in_context:,} ({ctx_perc:.2f}%)")
    print(f" [Attachment] in Output:  {attachment_in_output:,} ({out_perc:.2f}%)")
    print("="*30)

if __name__ == "__main__":
    analyze_baseline()
