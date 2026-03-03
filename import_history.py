import asyncio
import os
import re
import sys

# Ensure we can import nanobot
sys.path.append(os.getcwd())

from nanobot.agent.vector_memory import VectorMemoryStore
from nanobot.config.loader import load_config


async def import_history():
    config = load_config()
    workspace = config.workspace_path
    history_file = workspace / "memory" / "HISTORY.md"

    if not history_file.exists():
        print(f"History file {history_file} not found.")
        return

    print(f"Reading history from {history_file}...")
    content = history_file.read_text(encoding="utf-8")

    # Split by the timestamp pattern [YYYY-MM-DD HH:MM]
    # Using a safer regex split
    entries = re.split(r'\n(?=\[\d{4}-\d{2}-\d{2} \d{2}:\d{2}\])', content)

    vector_store = VectorMemoryStore(config.agents.defaults.vector_memory)

    print(f"Found {len(entries)} entries. Importing to vector DB...")

    count = 0
    for entry in entries:
        entry = entry.strip()
        if not entry:
            continue
        try:
            await vector_store.add_memory(entry)
            count += 1
            if count % 10 == 0:
                print(f"Imported {count} entries...")
        except Exception as e:
            print(f"Error importing entry: {e}")

    print(f"Done! Successfully imported {count} entries.")

if __name__ == "__main__":
    asyncio.run(import_history())
