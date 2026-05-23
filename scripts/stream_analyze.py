import json
import os
import glob
import re

"""
Stream Analyze: High-Speed Regex Count Utility
---------------------------------------------
This utility scans massive raw JSON files and counts messages linked to 
a specific User ID without needing a database.

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

# Directory to scan for raw JSON files (strictly using /output)
SEARCH_DIRS = [os.path.join(BASE_DIR, "output")]

def stream_parse_messages(file_path):
    user_msg_count = 0
    total_msg_count = 0
    
    # Pre-compile the regex patterns
    author_pattern = re.compile(r'"author":\s*{\s*"id":\s*"' + USER_ID + r'"')
    msg_start_pattern = re.compile(r'\{\s*"id":\s*"\d+"')

    try:
        # Read the file in 10MB chunks
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            chunk_size = 10 * 1024 * 1024
            while True:
                chunk = f.read(chunk_size)
                if not chunk:
                    break
                total_msg_count += len(msg_start_pattern.findall(chunk))
                user_msg_count += len(author_pattern.findall(chunk))
    except Exception as e:
        print(f"Error parsing {file_path}: {e}")

    return user_msg_count, total_msg_count

def analyze_all():
    if USER_ID == "YOUR_DISCORD_ID_HERE":
        print("ERROR: USER_ID not found in .env. Please set it before running.")
        return

    all_files = []
    for d in SEARCH_DIRS:
        if os.path.exists(d):
            all_files.extend(glob.glob(os.path.join(d, "*.json")))
    
    total_user_messages = 0
    total_messages = 0
    
    print(f"Starting analysis on {len(all_files)} raw files...")
    
    for f in all_files:
        u_count, t_count = stream_parse_messages(f)
        print(f" - {os.path.basename(f)}: {u_count:,} target / {t_count:,} total")
        total_user_messages += u_count
        total_messages += t_count
        
    print("\n--- MASTER ANALYSIS SUMMARY ---")
    print(f"Total messages scanned: {total_messages:,}")
    print(f"Total messages from target ID: {total_user_messages:,}")

if __name__ == "__main__":
    analyze_all()
