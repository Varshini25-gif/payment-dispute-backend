from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from .validator import RuleValidationError


def load_rules_from_yaml(path: str | Path) -> list[dict[str, Any]]:
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Rules file not found at {path}")

    try:
        with path.open("r", encoding="utf-8") as stream:
            document = yaml.safe_load(stream)
    except yaml.YAMLError as exc:
        raise RuleValidationError(f"Cannot parse YAML rule file at {path}: {exc}") from exc

    if document is None:
        return []

    rules: Any
    if isinstance(document, dict) and "rules" in document:
        rules = document["rules"]
    else:
        rules = document

    if not isinstance(rules, list):
        raise RuleValidationError(
            "Rule YAML must contain a top-level list of rules or an object with a 'rules' list."
        )

    return rules
