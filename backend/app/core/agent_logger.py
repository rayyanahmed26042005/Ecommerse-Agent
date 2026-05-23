"""Core logging utility for agentic AI flow and chat interactions."""

from __future__ import annotations

import datetime
import json
import os
import threading
from pathlib import Path
from typing import Any

# Resolve backend root directory to store logs.txt
BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
LOG_FILE_PATH = BACKEND_DIR / "logs.txt"

# Thread safety lock
_log_lock = threading.Lock()

def write_to_log_file(entry: str) -> None:
    """Thread-safe append to logs.txt file."""
    with _log_lock:
        try:
            # Ensure the directory exists
            LOG_FILE_PATH.parent.mkdir(parents=True, exist_ok=True)
            with open(LOG_FILE_PATH, "a", encoding="utf-8") as f:
                f.write(entry + "\n")
        except Exception as e:
            # Prevent logging errors from crashing the main application flow
            print(f"Error writing to logs.txt: {e}")

def format_event(event_type: str, details: Any, task_id: str | None = None) -> str:
    """Format log entry cleanly for high readability."""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    task_prefix = f" [TASK: {task_id}]" if task_id else ""
    
    separator = "=" * 80
    header = f"{separator}\n[{timestamp}]{task_prefix} EVENT: {event_type}\n"
    
    # Process details
    details_str = ""
    if isinstance(details, dict):
        # Format dictionary keys nicely
        for k, v in details.items():
            if isinstance(v, (dict, list)):
                formatted_val = json.dumps(v, indent=2, default=str)
                # Indent nested values
                indented_val = "\n".join("    " + line for line in formatted_val.splitlines())
                details_str += f"  {k}:\n{indented_val}\n"
            else:
                details_str += f"  {k}: {v}\n"
    elif isinstance(details, list):
        for idx, item in enumerate(details):
            details_str += f"  [{idx}]: {item}\n"
    else:
        details_str += f"  {details}\n"
        
    footer = "=" * 80 + "\n"
    return f"{header}{details_str}{footer}"

def log_event(event_type: str, details: Any, task_id: str | None = None) -> None:
    """Log any event in the chat or agent flow and append it to logs.txt."""
    entry = format_event(event_type, details, task_id)
    write_to_log_file(entry)
