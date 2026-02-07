# use _ prefix for private functions to avoid namespace pollution and signal that they are not part of the public API

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict
import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
CONFIGS_DIR = REPO_ROOT / "configs"

# read_yaml is a private function that reads a YAML file and returns its contents as a dictionary. 
# It raises an error if the file does not exist or if the contents are not a dictionary.
def _read_yaml(path: Path) -> Dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Configuration file not found: {path}")
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise ValueError(f"Configuration file must contain a dictionary at the top level: {path}") 
    return data

def _deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    """
    base is the original dictionary that we want to merge into. 
    however, key:value pairs in base can be overriden by the override key:value pairs where base.key = override.key.
     - if the value is a dictionary, we recursively merge the dictionaries
    This is used to establish a hierarchy of configuration files, where more specific files can override values from more general files.
    """

    # dict(base) creates an internal copy of the base dictionary
    # avoids mutating the original, normalized inputs, and signals intent for mutation within this function
    base_clone = dict(base)
    for key, value in override.items():
        if key in base_clone and isinstance(base_clone[key], dict) and isinstance(value, dict):
            # Yes, the function is recursive. If both the base and override values for a key are dictionaries, we merge them recursively.
            # and yes, this is a common pattern for deep merging dictionaries in Python.
            base_clone[key] = _deep_merge(base_clone[key], value)
        else:
            base_clone[key] = value
    return base_clone

def load_config(universe: str, content: str, execution: str) -> Dict[str, Any]:
    paths = [
        CONFIGS_DIR / "execution" / "Default.yaml",
        CONFIGS_DIR / "execution" / f"{execution}.yaml",
        CONFIGS_DIR / "content" / f"{content}.yaml",
        CONFIGS_DIR / "universes" / f"{universe}.yaml",
    ]

    merged: Dict[str, Any] = {}
    for path in paths:
        config = _read_yaml(path)
        merged = _deep_merge(merged, config)

    # Create _metadata for this run and attach it to the merged config. This will be useful for logging, debugging, and reproducibility.
    merged.setdefault("_meta", {})
    merged["_meta"]["universe"] = universe
    merged["_meta"]["content"] = content
    # notice that uniquely, execution is the only config that is subject to an override, all others are additive
    merged["_meta"]["execution"] = execution
    merged["_meta"]["sources"] = [str(path.relative_to(REPO_ROOT)) for path in paths]

    return merged