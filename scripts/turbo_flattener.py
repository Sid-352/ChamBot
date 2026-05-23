import os
import glob
import json
import re

"""
Turbo Flattener: Memory-Efficient JSON to NDJSON Converter
---------------------------------------------------------
This script converts massive Discord JSON exports (20GB+) into 
Newline-Delimited JSON (NDJSON/JSONL).

Paths are calculated relative to this script's location.
"""

# Calculate the project root relative to this script (in /scripts)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Input directories containing raw Discord JSON exports (strictly using /output)
SEARCH_DIRS = [os.path.join(BASE_DIR, "output")]
# Output directory for the flattened .jsonl files
JSONL_DIR = os.path.join(BASE_DIR, "flattened_data")

def turbo_flatten():
    # Ensure the output directory exists
    os.makedirs(JSONL_DIR, exist_ok=True)
    
    # Collect all JSON files from the search paths
    json_files = []
    for d in SEARCH_DIRS:
        if os.path.exists(d):
            json_files.extend(glob.glob(os.path.join(d, "*.json")))
        
    print(f"Found {len(json_files)} files. Starting Turbo Flattener...")
        
    for f in json_files:
        file_name = os.path.basename(f)
        out_file = os.path.join(JSONL_DIR, file_name.replace(".json", ".jsonl"))
        
        # Skip files that have already been processed
        if os.path.exists(out_file):
            print(f"Skipping (already flattened): {file_name}")
            continue
            
        # Extract the Channel ID from the filename (standard DiscordChatExporter format)
        channel_id_match = re.search(r'\[(\d+)\]', file_name)
        channel_id = channel_id_match.group(1) if channel_id_match else ""

        print(f"Flattening: {file_name}...")
        count = 0
        
        # Open input file for streaming and output file for writing
        with open(f, 'r', encoding='utf-8', errors='ignore') as f_in, \
             open(out_file, 'w', encoding='utf-8') as f_out:
            
            # Fast-forward until I hit the start of the "messages" array
            for line in f_in:
                if '"messages": [' in line:
                    break
                    
            # Extract each message block line-by-line
            buffer = []
            in_message = False
            
            for line in f_in:
                # DiscordChatExporter always starts a message block with exactly 4 spaces and a {
                if line.startswith("    {"):
                    in_message = True
                    buffer = [line]
                    continue
                    
                if in_message:
                    buffer.append(line)
                    # A message block ends with 4 spaces and a }, or } (for the last item)
                    if line.startswith("    },") or line.startswith("    }"):
                        msg_str = "".join(buffer)
                        
                        # Strip trailing comma and newline to make it valid standalone JSON
                        if msg_str.endswith(',\n'):
                            msg_str = msg_str[:-2]
                        elif msg_str.endswith('}\n'):
                            msg_str = msg_str[:-1]
                            
                        try:
                            # Parse this single message block
                            m = json.loads(msg_str)
                            
                            # Handle empty content (images/embeds) by labeling as [Attachment]
                            content = m.get("content")
                            if not content:
                                content = "[Attachment]"
                                
                            author = m.get("author") or {}
                            ref = m.get("reference") or {}
                            
                            # Build the flattened message dictionary
                            flat_msg = {
                                "id": m.get("id"),
                                "timestamp": m.get("timestamp"),
                                "author_id": author.get("id"),
                                "author_name": author.get("name"),
                                "content": content,
                                "channel_id": channel_id,
                                "reply_id": ref.get("messageId")
                            }
                            
                            # Write as a single line in the .jsonl file
                            f_out.write(json.dumps(flat_msg) + '\n')
                            count += 1
                            
                        except Exception:
                            # Ignore any malformed or truncated message blocks
                            pass 
                            
                        in_message = False
                        buffer = []

        print(f" -> Success! Flattened {count:,} messages.")

if __name__ == "__main__":
    turbo_flatten()
