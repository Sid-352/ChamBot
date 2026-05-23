import duckdb
import os
import glob
import json
import re

"""
Dataset Generator: High-Speed SQL Context Mapping
---------------------------------------------------------
This script generates the final training dataset. It uses 
DuckDB to perform relational joins and window functions over 
millions of messages.

Configuration is loaded from the project root .env file.
Paths are calculated relative to this script's location.
"""

# Calculate the project root relative to this script (in /scripts)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def load_env():
    """Simple parser to load variables from .env without external dependencies."""
    env_vars = {}
    env_path = os.path.join(BASE_DIR, ".env")
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            for line in f:
                if '=' in line and not line.startswith('#'):
                    k, v = line.strip().split('=', 1)
                    env_vars[k] = v
    return env_vars

# Load configuration
env = load_env()
USER_ID = env.get("USER_ID", "YOUR_DISCORD_ID_HERE")

# --- Configuration ---
INPUT_DIR = os.path.join(BASE_DIR, "flattened_data")
OUTPUT_FILE = os.path.join(BASE_DIR, "data", "final_dataset.jsonl")
DB_PATH = os.path.join(BASE_DIR, "temp_storage.db")
TEMP_DIR = os.path.join(BASE_DIR, "logs", "tmp")

def clean_text(text):
    """Sanitizes text by removing raw Discord pings and URLs."""
    if not text: return ""
    text = re.sub(r'<@!?\d+>', '[User]', text) 
    text = re.sub(r'http\S+', '', text) 
    return text.strip()

def run_extraction():
    if USER_ID == "YOUR_DISCORD_ID_HERE":
        print("ERROR: USER_ID not found in .env. Please set it before running.")
        return

    # Setup directories
    os.makedirs(TEMP_DIR, exist_ok=True)
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    
    # Connect to DuckDB
    db = duckdb.connect(DB_PATH)
    clean_temp_dir = TEMP_DIR.replace('\\', '/')

    # Performance and Memory Tuning
    db.execute("SET memory_limit='4GB'")
    db.execute(f"PRAGMA temp_directory='{clean_temp_dir}'")
    db.execute("SET threads=1")
    db.execute("SET preserve_insertion_order=false")
    
    # Initialize Table
    print("Initializing Database...")
    db.execute("DROP TABLE IF EXISTS raw_messages")
    db.execute("""
        CREATE TABLE raw_messages (
            id VARCHAR, 
            timestamp TIMESTAMP, 
            author_id VARCHAR, 
            author_name VARCHAR, 
            content VARCHAR, 
            channel_id VARCHAR, 
            reply_id VARCHAR
        )
    """)
    
    # Ingest Flattened Data
    jsonl_files = glob.glob(os.path.join(INPUT_DIR, "*.jsonl"))
    print(f"Ingesting {len(jsonl_files)} files...")
    for f in jsonl_files:
        clean_path = f.replace("'", "''")
        try:
            db.execute(f"INSERT INTO raw_messages SELECT * FROM read_json_auto('{clean_path}', ignore_errors=true)")
        except Exception as e:
            print(f"   [ERROR] Failed to ingest {os.path.basename(f)}: {e}")

    # Context Mapping Query
    print("Mapping conversation context...")
    extraction_query = f"""
        WITH sorted_msgs AS (
            SELECT 
                id, timestamp, author_id, author_name, content, channel_id, reply_id,
                LAG(author_name || ': ' || content, 3) OVER (PARTITION BY channel_id ORDER BY timestamp) as p3,
                LAG(author_name || ': ' || content, 2) OVER (PARTITION BY channel_id ORDER BY timestamp) as p2,
                LAG(author_name || ': ' || content, 1) OVER (PARTITION BY channel_id ORDER BY timestamp) as p1,
                LEAD(author_name || ': ' || content, 1) OVER (PARTITION BY channel_id ORDER BY timestamp) as f1,
                LEAD(author_name || ': ' || content, 2) OVER (PARTITION BY channel_id ORDER BY timestamp) as f2,
                LEAD(author_name || ': ' || content, 3) OVER (PARTITION BY channel_id ORDER BY timestamp) as f3
            FROM raw_messages
        )
        SELECT 
            s.*,
            r.author_name as reply_target_author,
            r.content as reply_target_content
        FROM sorted_msgs s
        LEFT JOIN raw_messages r ON s.reply_id = r.id
        WHERE s.author_id = '{USER_ID}'
        AND s.content IS NOT NULL 
        AND s.content != '[Attachment]'
        AND LENGTH(s.content) > 1
        ORDER BY s.timestamp
    """

    results = db.execute(extraction_query).fetchall()
    print(f"Found {len(results):,} target interactions. Generating training file...")

    # Write formatted JSONL
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as out:
        for row in results:
            ctx_block = []
            
            # Add reply target
            if row[13] and row[14]:
                ctx_block.append(f"[Replying to {row[13]}]: {row[14]}")
            
            # Add preceding context
            for p in [row[7], row[8], row[9]]:
                if p: ctx_block.append(p)
            
            # Add future context
            for f in [row[10], row[11], row[12]]:
                if f: ctx_block.append(f"[Future Context] {f}")

            # Define instruction
            if ctx_block:
                chat_history = "\n".join(ctx_block)
                instruction = f"Chat Context:\n{chat_history}\n\nRespond to the conversation as Chameleon:"
            else:
                instruction = "Start a new conversation as Chameleon."

            # Final Output Prep
            clean_output = clean_text(row[4])
            json_line = {"instruction": instruction, "input": "", "output": clean_output}
            
            # Recency Weighting
            year = row[1].year
            weight = 3 if year >= 2025 else (2 if year == 2024 else 1)
            for _ in range(weight):
                out.write(json.dumps(json_line) + '\n')

    print(f"SUCCESS! Master dataset saved to: {os.path.abspath(OUTPUT_FILE)}")
    db.close()

if __name__ == "__main__":
    run_extraction()
