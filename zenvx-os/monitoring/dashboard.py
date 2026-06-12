#!/usr/bin/env python3
"""dashboard.py - live terminal dashboard for ZenvX metrics."""
import json
import os
import time

CURRENT = "/var/lib/zenvx/metrics/current.json"
CYAN = "\033[38;2;0;255;204m"
DIM = "\033[2m"
BOLD = "\033[1m"
RESET = "\033[0m"
CLEAR = "\033[2J\033[H"


def bar(percent, width=30):
    filled = int(width * min(max(percent, 0), 100) / 100)
    return "\u2588" * filled + "\u2591" * (width - filled)


def load():
    try:
        with open(CURRENT) as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def render(m):
    lines = [CLEAR, f"{CYAN}{BOLD}  ZENVX OS - Live Dashboard{RESET}", ""]
    lines.append(f"  Uptime:   {m.get('uptime_s', 0)} s")
    lines.append(f"  Requests: {m.get('requests', 0)}  "
                 f"Errors: {m.get('errors', 0)}")
    lines.append("")
    cpu = m.get("cpu_percent", 0.0)
    ram = m.get("ram_percent", 0.0)
    lines.append(f"  CPU  [{CYAN}{bar(cpu)}{RESET}] {cpu:5.1f}%")
    lines.append(f"  RAM  [{CYAN}{bar(ram)}{RESET}] {ram:5.1f}%  "
                 f"({m.get('ram_used_mb', 0)}/{m.get('ram_total_mb', 0)} MB)")
    lines.append("")
    lines.append(f"  Tokens/sec: {CYAN}{m.get('avg_tokens_per_second', 0)}{RESET}")
    lines.append(f"  Latency:    {m.get('avg_latency_s', 0)} s")
    lines.append("")
    lines.append(f"{DIM}  Press Ctrl+C to exit. Refreshing every 2s.{RESET}")
    return "\n".join(lines)


def main():
    try:
        while True:
            print(render(load()))
            time.sleep(2)
    except KeyboardInterrupt:
        print("\nDashboard closed.")


if __name__ == "__main__":
    main()
