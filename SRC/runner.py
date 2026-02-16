from __future__ import annotations

import argparse
import yaml
from pathlib import Path

from SRC.config import load_config
from SRC.validation import validate_config, ConfigError
from SRC.run_context import RunContext
from SRC.schema_registry import SchemaRegistry
from SRC.providers.dummy_fundamentals import DummyFundamentalsProvider, write_statement_csv

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

    try:
        validate_config(config)
    except ConfigError as e:
        print(f"[CONFIG ERROR] {e}")
        raise SystemExit(2)

    outputs_root = Path("outputs")
    run_context = RunContext.create(config, outputs_root)

    # load schema registry
    repo_root = Path(".").resolve()
    registry = SchemaRegistry.load(repo_root)

    symbols = run_context.config["universe"]["symbols"]
    provider = DummyFundamentalsProvider()
    bundle = provider.fetch(symbols) # in essense, created the basecase dummy variables

    with open(run_context.output_dir / "config.yaml", "w", encoding="utf-8") as f:
        yaml.safe_dump(config, f, sort_keys=False)

    should_abort = False

    try:

        # validate + write artifacts
        profile = run_context.config["execution"].get("schema_profile", "debug_strict")
        strict_profiles = {"debug_strict"}
        is_strict = profile in strict_profiles

        diagnostics = {
            "schema_version": registry.schema.get("version"),
            "profile": profile,
            "provider": provider.__class__.__name__,
            "summary": {
                "status": "success",
                "total_records_checked": 0,
                "missing_total": 0,
                "errors": 0,
                "warnings": 0
            },
            "details": {
                "balance_sheet": [],
                "income_statement": [],
                "cash_flow_statement": []
            }
        }

        for statement_name, records in bundle.items():
            for record in records:
                diagnostics["summary"]["total_records_checked"] += 1
                missing = registry.validate_record(profile, statement_name, record)
                if missing:
                    diagnostics["summary"]["missing_total"] += len(missing)
                    severity = "error" if is_strict else "warning"
                    if severity == "error":
                        diagnostics["summary"]["errors"] += 1
                    else:
                        diagnostics["summary"]["warnings"] += 1

                    diagnostics["details"].setdefault(statement_name, []).append({
                        "symbol": record.get("symbol"),
                        "period_end": record.get("period_end"),
                        "missing": missing,
                        "severity": severity
                    })

        if diagnostics["summary"]["errors"] > 0:
            diagnostics["summary"]["status"] = "failed"
            should_abort = True
        elif diagnostics["summary"]["warnings"] > 0:
            diagnostics["summary"]["status"] = "degraded"
        else:
            diagnostics["summary"]["status"] = "success"
        
        if not should_abort:
            for statement_name, records in bundle.items():
                out_path = write_statement_csv(run_context.output_dir, statement_name, records)
                print(f"[OK] Wrote {statement_name}: {out_path}")
    
    finally:
        diagnostics_path = run_context.output_dir / "diagnostics.yaml"
        with open(diagnostics_path, "w", encoding="utf-8") as f:
            yaml.safe_dump(diagnostics, f, sort_keys=False)
        print(f"[OK] Diagnostics written: {diagnostics_path}")
    
    if should_abort:
        raise SystemExit("[SCHEMA ERROR] Strict profile validation failed. Missing required fields detected. See diagnostics.yaml for details.")

    print(f"[OK] Run created: {run_context.run_id}")
    print(f"[OK] Output dir: {run_context.output_dir}")

    # we return 0 to indicate successful execution. Apparently unix did this to us.
    return 0

if __name__ == "__main__":
    raise SystemExit(main())