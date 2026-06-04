from pathlib import Path

import pytest

from app.services.rule_engine.loader import load_rules_from_yaml
from app.services.rule_engine.parser import parse_rules, Rule
from app.services.rule_engine.validator import RuleValidationError, validate_rule_syntax

VALID_RULE_YAML = """
rules:
  - id: "rule-1"
    description: "Sample rule"
    conditions:
      all_of:
        - field: transaction_amount
          operator: gt
          value: 100
        - field: status
          operator: equals
          value: "pending"
    actions:
      - type: "flag"
        message: "High-value pending transaction"
"""

INVALID_RULE_YAML = """
- id: 1
  conditions:
    field: transaction_amount
    operator: gt
    value: 100
  actions:
    - type: "flag"
"""


def test_load_rules_from_yaml_reads_rules_from_file(tmp_path: Path) -> None:
    rules_file = tmp_path / "rules.yaml"
    rules_file.write_text(VALID_RULE_YAML, encoding="utf-8")

    raw_rules = load_rules_from_yaml(rules_file)

    assert isinstance(raw_rules, list)
    assert raw_rules[0]["id"] == "rule-1"


def test_load_rules_from_yaml_rejects_invalid_yaml(tmp_path: Path) -> None:
    rules_file = tmp_path / "rules.yaml"
    rules_file.write_text("::: invalid yaml :::", encoding="utf-8")

    with pytest.raises(RuleValidationError):
        load_rules_from_yaml(rules_file)


def test_validate_rule_syntax_raises_on_missing_id() -> None:
    with pytest.raises(RuleValidationError, match="non-empty 'id'"):
        validate_rule_syntax({"conditions": {}, "actions": []})


def test_parse_rules_returns_rule_objects() -> None:
    raw_rules = [
        {
            "id": "rule-1",
            "description": "Sample rule",
            "conditions": {
                "field": "status",
                "operator": "equals",
                "value": "approved",
            },
            "actions": [{"type": "notify", "message": "Approved"}],
        }
    ]

    parsed_rules = parse_rules(raw_rules)

    assert len(parsed_rules) == 1
    assert isinstance(parsed_rules[0], Rule)
    assert parsed_rules[0].id == "rule-1"
    assert parsed_rules[0].conditions["field"] == "status"


def test_parse_rules_reports_invalid_rule() -> None:
    raw_rules = [
        {
            "id": "rule-1",
            "conditions": {"field": "status", "operator": "invalid", "value": "approved"},
            "actions": [{"type": "notify"}],
        }
    ]

    with pytest.raises(RuleValidationError, match="operator"):
        parse_rules(raw_rules)
