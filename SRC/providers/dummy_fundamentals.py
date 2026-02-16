from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any, Dict, List
import csv


@dataclass(frozen=True)
class DummyFundamentalsProvider:
    """
    Emits canonical BS/IS/CF records for a small number of periods.
    Deterministic, for smoke tests.
    """
    source: str = "dummy"

    def fetch(self, symbols: List[str]) -> Dict[str, List[Dict[str, Any]]]:

        periods = ["2025-12-31", "2024-12-31", "2023-12-31"]

        output = {
            "balance_sheet": [],
            "income_statement": [],
            "cash_flow_statement": []
        }

        for symbol in symbols:
            for period in periods:
                common = {
                    "symbol": symbol,
                    "period_end": period,
                    "period_type": "annual",
                    "currency": "USD",
                    "source": self.source
                    }

                output["balance_sheet"].append({
                    **common,
                    "cash_and_equivalents": 1000.0,
                    "total_assets": 5000.0,
                    "total_liabilities": 3000.0,
                    "total_equity": 2000.0,
                    "total_debt": 1500.0})
                
                output["income_statement"].append({
                    **common,
                    "revenue": 2000.0,
                    "operating_income": 500.0,
                    "net_income": 300.0,
                    "cost_of_goods_sold": 1200.0,
                    "gross_profit": 800.0,
                    "operating_expenses": 300.0})
                
                
                cfo = 1100.0
                capex = -400.0
                output["cash_flow_statement"].append({
                    **common,
                    "cfo": cfo,
                    "capex": capex,
                    "free_cash_flow": cfo + capex})
                
        return output
    
def write_statement_csv(output_dir, statement_name: str, records: List[Dict[str, Any]]):
    path = output_dir / f"{statement_name}.csv"
    if not records:
        # still create an empty file for now
        path.write_text("", encoding="utf-8")
        return str(path)
    
    common_cols = ["symbol", "period_end", "period_type", "currency", "source"]
    extra_cols = sorted([k for k in records[0].keys() if k not in common_cols])
    total_columns = common_cols + extra_cols

    with path.open("w", newline="", encoding="utf-8") as file:
        written = csv.DictWriter(file, fieldnames = total_columns)
        written.writeheader()
        written.writerows(records)

    return str(path)