from unsloth import FastLanguageModel
import torch
import os

"""
Local Merge Script: Finalizing the Digital Clone
-----------------------------------------------
This script merges LoRA adapters into the base Llama 3.1 model 
and exports the result to GGUF.

Hardware Note: 
Merging requires approximately 16GB of System RAM. 

Paths are calculated relative to this script's location.
"""

# Calculate the project root relative to this script (in /scripts)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Path to the folder containing uncompressed model weights
CHECKPOINT_PATH = os.path.join(BASE_DIR, "checkpoint")
# Path where the final GGUF file is saved
OUTPUT_PATH = os.path.join(BASE_DIR, "models")

def local_merge():
    os.makedirs(OUTPUT_PATH, exist_ok=True)
    
    if not os.path.exists(CHECKPOINT_PATH):
        print(f"ERROR: Checkpoint folder not found at {CHECKPOINT_PATH}")
        return

    print("Loading base model and applying trained weights...")
    
    # Load the base model and apply the adapters from the checkpoint
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name = CHECKPOINT_PATH,
        max_seq_length = 2048,
        load_in_4bit = True,
    )

    print("Weights applied. Exporting to GGUF (Q3_K_M)...")

    # Export to GGUF for local inference
    model.save_pretrained_gguf(
        os.path.join(OUTPUT_PATH, "model_final"), 
        tokenizer, 
        quantization_method = "q3_k_m"
    )

    print(f"\nSUCCESS! The digital clone is ready at: {OUTPUT_PATH}")
    print("Next Move: Load the .gguf file into the inference engine.")

if __name__ == "__main__":
    local_merge()
