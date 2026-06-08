from pathlib import Path

import pytest

from app.services.rule_engine.engine import RuleEngine, decide_routing
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


def test_rule_engine_matches_amount_range_dispute_type_and_payer_id() -> None:
    raw_rules = [
        {
            "id": "route-high-risk",
            "description": "Route high-risk disputes",
            "conditions": {
                "all_of": [
                    {"field": "amount", "operator": "in", "value": [100, 200]},
                    {"field": "type", "operator": "equals", "value": "chargeback"},
                    {"field": "payer_id", "operator": "in", "value": ["payer-123", "payer-456"]},
                ]
            },
            "actions": [{"type": "route", "target": "special-investigation"}],
        }
    ]

    rules = parse_rules(raw_rules)
    engine = RuleEngine(rules)

    dispute_context = {"amount": 150, "type": "chargeback", "payer_id": "payer-123"}
    matches = engine.get_matching_rules(dispute_context)

    assert len(matches) == 1
    assert matches[0].rule_id == "route-high-risk"
    assert matches[0].actions[0]["target"] == "special-investigation"


def test_decide_routing_returns_first_match() -> None:
    raw_rules = [
        {
            "id": "route-fraud",
            "conditions": {"field": "type", "operator": "equals", "value": "fraud"},
            "actions": [{"type": "route", "target": "fraud-team"}],
        },
        {
            "id": "route-other",
            "conditions": {"field": "type", "operator": "equals", "value": "other"},
            "actions": [{"type": "route", "target": "default-team"}],
        },
    ]

    rules = parse_rules(raw_rules)
    decision = decide_routing(rules, {"type": "fraud"})

    assert decision is not None
    assert decision.rule_id == "route-fraud"
    assert decision.actions[0]["target"] == "fraud-team"


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


def test_rule_engine_matches_amount_ranges() -> None:
    rule = Rule(
        id="amount-range",
        description="Route high value disputes",
        conditions={
            "all_of": [
                {"field": "amount", "operator": "gte", "value": 500},
                {"field": "amount", "operator": "lte", "value": 2000},
            ]
        },
        actions=[{"type": "route", "parameters": {"queue": "high_value"}}],
    )

    from app.services.rule_engine.engine import RuleEngine

    engine = RuleEngine([rule])
    match = engine.decide({"amount": 1500, "type": "chargeback", "customer_id": "payer-1"})

    assert match is not None
    assert match.rule_id == "amount-range"
    assert match.actions[0]["type"] == "route"
    assert match.actions[0]["parameters"]["queue"] == "high_value"


def test_rule_engine_matches_dispute_type_and_payer_id() -> None:
    rule = Rule(
        id="priority-dispute",
        description="Route disputes for VIP payer and chargebacks",
        conditions={
            "all_of": [
                {"field": "type", "operator": "equals", "value": "chargeback"},
                {"field": "customer_id", "operator": "in", "value": ["payer-1", "payer-2"]},
            ]
        },
        actions=[{"type": "route", "parameters": {"queue": "vip_chargebacks"}}],
    )

    from app.services.rule_engine.engine import RuleEngine

    engine = RuleEngine([rule])
    match = engine.decide({"amount": 1200, "type": "chargeback", "customer_id": "payer-1"})

    assert match is not None
    assert match.rule_id == "priority-dispute"
    assert match.actions[0]["parameters"]["queue"] == "vip_chargebacks"


def test_rule_engine_returns_no_match_when_conditions_fail() -> None:
    rule = Rule(
        id="low-value",
        description="Only match low value disputes",
        conditions={"field": "amount", "operator": "lt", "value": 100},
        actions=[{"type": "route", "parameters": {"queue": "low_value"}}],
    )

    from app.services.rule_engine.engine import RuleEngine

    engine = RuleEngine([rule])
    match = engine.decide({"amount": 200, "type": "chargeback", "customer_id": "payer-1"})

    assert match is None
