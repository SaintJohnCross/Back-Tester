from __future__ import annotations

import argparse
import yaml

from config import load_config

def parse_args() -> argparse.Namespace:
    """
    This function uses argparse to parse command-line arguments for the backtester. It expects three required arguments: universe, content, and execution. 
    Each of these corresponds to a specific configuration that will be loaded and merged to run the backtest.
    """
    parser = argparse.ArgumentParser(description="Run the backtester with specified universe, content, and execution configurations.")
    parser.add_argument("--universe", type=str, required=True, help="The universe configuration to use (e.g., US_Smoke).")
    parser.add_argument("--content", type=str, required=True, help="The content configuration to use (e.g., fundamentals).")
    parser.add_argument("--execution", type=str, required=True, help="The execution configuration to use (e.g., prod).")
    return parser.parse_args()

def main() -> int:
    args = parse_args()
    config = load_config(args.universe, args.content, args.execution)
    print(yaml.safe_dump(config, sort_keys=False))
    # we return 0 to indicate successful execution. Apparently unix did this to us.
    return 0

if __name__ == "__main__":
    raise SystemExit(main())