from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict
from datetime import datetime

@dataclass(frozen=True)
class RunContext:
    run_id: str
    config: Dict[str, Any]
    output_dir: Path

    @staticmethod
    def create(config: Dict[str, Any], outputs_root: Path) -> "RunContext":
        run_id = datetime.utcnow().strftime("%Y-%m-%dT%H-%M-%SZ")
        output_dir = outputs_root / "Runs" / run_id
        output_dir.mkdir(parents=True, exist_ok=False)
        return RunContext(run_id=run_id, config=config, output_dir=output_dir)
