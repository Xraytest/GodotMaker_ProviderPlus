#!/usr/bin/env python3
"""SubagentStop dispatcher: log lifecycle event, then validate report.

Single entry point for the SubagentStop hook. Reads stdin once and passes
the data to both handlers serially:
  1. log_subagent.handle_stop  — record metrics + save traces (never blocks)
  2. check_worker_report.main_with_data — validate report (may block)

This avoids the race condition that occurs when Claude Code runs multiple
SubagentStop hooks in parallel: log_subagent reads metrics_current.jsonl
while check_worker_report writes to it, causing JSONDecodeError crashes.
"""
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def main():
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        sys.exit(0)

    if data.get("hook_event_name") != "SubagentStop":
        sys.exit(0)

    # Dump raw hook data for debugging C/F investigations
    from log_subagent import _debug
    _debug(f"SubagentStop raw keys: {sorted(data.keys())}")
    for k, v in data.items():
        if k == "last_assistant_message":
            _debug(f"  {k}: type={type(v).__name__} len={len(v or '')}")
        else:
            _debug(f"  {k}: {v!r}")

    # 1. Log lifecycle event (never blocks)
    from log_subagent import handle_stop
    handle_stop(data)

    # 2. Validate report (may block via sys.exit(1))
    from check_worker_report import main_with_data
    main_with_data(data)


if __name__ == "__main__":
    main()
