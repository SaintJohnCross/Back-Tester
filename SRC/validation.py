from __future__ import annotations

from typing import Any, Dict, List

class ConfigError(Exception):
    """Custom exception for configuration errors."""
    pass

def _require(config: Dict[str, Any], path: str) -> Any:
    """
    Fetch config["a"]["b"]["c"] given a path like "a.b.c"
    Raises ConfigError if any part of the path is missing.
    """

    current: Any = config
    for part in path.split("."):
        if not isinstance(current, dict) or part not in current:
            raise ConfigError(f"Missing required config key: '{path}'")
        current = current[part]

    return current

def validate_config(config: Dict[str, Any]) -> None:
    # Required top-level key-values
    _require(config, "execution")
    _require(config, "universe")
    _require(config, "content")

    # Execution checks within specific key-value pairs
    logging = _require(config, "execution.logging")
    if logging not in {"minimal", "maximal"}:
        raise ConfigError(f"Invalid logging level: '{logging}'. Must be 'minimal' or 'maximal'.")

    data_mode = _require(config, "execution.data_mode")
    if data_mode not in {"dummy", "production"}:
        raise ConfigError(f"Invalid data mode: '{data_mode}'. Must be 'dummy' or 'production'.")

    run_scale = _require(config, "execution.run_scale")
    if run_scale not in {"full", "smoke", "sample"}:
        raise ConfigError(f"Invalid run scale: '{run_scale}'. Must be 'full', 'smoke', or 'sample'.")
    
    error_policy = _require(config, "execution.error_policy")
    if error_policy not in {"fail_fast", "fail", "skip", "best_effort"}:
        raise ConfigError(f"Invalid error policy: '{error_policy}'. Must be 'fail_fast', 'fail', 'skip', or 'best_effort'.")
    
    # Universe checks within specific key-value pairs
    symbols = _require(config, "universe.symbols")
    if not isinstance(symbols, list) or len(symbols) == 0:
        raise ConfigError("universe.symbols must be a non-empty list")

    bad = [s for s in symbols if not isinstance(s, str) or not s.strip()]
    if bad:
        raise ConfigError("universe.symbols must contain only non-empty strings")

    # Protocol checks within specific key-value pairs
    protocol = _require(config, "content.protocol")
    if protocol not in {"fundamentals", "relative_valuations", "none"}:
        raise ConfigError("content.protocol must be 'fundamentals', 'relative_valuations', or 'none'")