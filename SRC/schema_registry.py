from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Set

import yaml


class SchemaError(Exception):
    pass


@dataclass(frozen=True)
class SchemaRegistry:
    schema: Dict[str, Any]

    @staticmethod
    def load(repo_root: Path) -> "SchemaRegistry":
        path = repo_root / "configs" / "schema" / "schema_main.yaml"
        if not path.exists():
            raise SchemaError(f"Schema file not found: {path}")

        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        if not isinstance(data, dict):
            raise SchemaError(f"Schema YAML must be a mapping at top-level: {path}")

        # Minimal sanity checks
        if "statements" not in data or "requirements" not in data:
            raise SchemaError("schema_main.yaml must contain 'statements' and 'requirements'")

        return SchemaRegistry(schema=data)

    def statements(self) -> List[str]:
        return list(self.schema["statements"].keys())

    def profiles(self) -> List[str]:
        return list(self.schema["requirements"].keys())

    def fields_for_statement(self, statement: str) -> Set[str]:
        st = self.schema["statements"].get(statement)
        if st is None:
            raise SchemaError(f"Unknown statement: {statement}")

        fields = st.get("fields")
        if not isinstance(fields, dict):
            raise SchemaError(f"Statement '{statement}' must contain a 'fields' mapping")

        return set(fields.keys())

    def required_fields(self, profile: str, statement: str) -> Set[str]:
        reqs = self.schema["requirements"].get(profile)
        if reqs is None:
            raise SchemaError(f"Unknown requirement profile: {profile}")

        common = reqs.get("common", [])
        specific = reqs.get(statement, [])

        if not isinstance(common, list) or not isinstance(specific, list):
            raise SchemaError(f"Requirements for profile '{profile}' must be lists")

        # Common fields + statement fields required by this profile
        required = set(common) | set(specific)

        # Optional guard: ensure statement-specific required fields exist in statement registry
        known = self.fields_for_statement(statement)
        unknown_required = [f for f in specific if f not in known]
        if unknown_required:
            raise SchemaError(
                f"Profile '{profile}' requires unknown fields for '{statement}': {unknown_required}"
            )

        return required

    def validate_record(self, profile: str, statement: str, record: Dict[str, Any]) -> List[str]:
        if not isinstance(record, dict):
            raise SchemaError("Record must be a dict")

        required = self.required_fields(profile, statement)
        missing = [k for k in sorted(required) if k not in record]
        return missing
