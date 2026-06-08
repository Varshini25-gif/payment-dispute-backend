from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional

from .evaluator import evaluate_condition
from .parser import Rule


@dataclass(frozen=True)
class RuleMatch:
    rule_id: str
    description: Optional[str]
    metadata: Optional[Dict[str, Any]]
    actions: List[Dict[str, Any]]


class RuleEngine:
    def __init__(self, rules: Iterable[Rule]) -> None:
        self.rules = list(rules)

    def get_matching_rules(self, context: Any, first_match: bool = False) -> List[RuleMatch]:
        matches: List[RuleMatch] = []
        for rule in self.rules:
            if evaluate_condition(rule.conditions, context):
                matches.append(
                    RuleMatch(
                        rule_id=rule.id,
                        description=rule.description,
                        metadata=rule.metadata,
                        actions=rule.actions,
                    )
                )
                if first_match:
                    break
        return matches

    def evaluate(self, context: Any, first_match: bool = False) -> List[RuleMatch]:
        return self.get_matching_rules(context, first_match=first_match)

    def decide(self, context: Any) -> Optional[RuleMatch]:
        matches = self.get_matching_rules(context, first_match=True)
        return matches[0] if matches else None


def evaluate_rules(rules: Iterable[Rule], context: Any, first_match: bool = False) -> List[RuleMatch]:
    return RuleEngine(rules).evaluate(context, first_match=first_match)


def decide_routing(rules: Iterable[Rule], context: Any) -> Optional[RuleMatch]:
    return RuleEngine(rules).decide(context)
