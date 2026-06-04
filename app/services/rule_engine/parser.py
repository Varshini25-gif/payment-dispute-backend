from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from .validator import RuleValidationError, validate_rule_syntax


@dataclass(frozen=True)
class Rule:
    id: str
    conditions: Dict[str, Any]
    actions: List[Dict[str, Any]]
    description: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


def parse_rules(raw_rules: list[dict[str, Any]]) -> list[Rule]:
    if not isinstance(raw_rules, list):
        raise TypeError("Raw rules must be a list of rule mappings.")

    parsed: list[Rule] = []
    for rule in raw_rules:
        try:
            validate_rule_syntax(rule)
        except RuleValidationError as exc:
            raise RuleValidationError(f"Invalid rule during parsing: {exc}") from exc

        parsed.append(
            Rule(
                id=rule["id"],
                description=rule.get("description"),
                conditions=rule["conditions"],
                actions=rule["actions"],
                metadata=rule.get("metadata"),
            )
        )

    return parsed
