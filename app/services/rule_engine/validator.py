from __future__ import annotations

from typing import Any


class RuleValidationError(ValueError):
    """Raised when a rule definition is syntactically invalid."""


VALID_TOP_LEVEL_KEYS = {"id", "description", "conditions", "actions", "metadata"}
VALID_CONDITION_KEYS = {"all_of", "any_of", "not", "field", "operator", "value"}
VALID_ACTION_KEYS = {"type", "parameters", "target", "message"}
VALID_OPERATORS = {
    "equals",
    "not_equals",
    "in",
    "not_in",
    "gt",
    "gte",
    "lt",
    "lte",
    "contains",
    "matches",
}


def validate_rule_syntax(rule: dict[str, Any]) -> None:
    if not isinstance(rule, dict):
        raise RuleValidationError("Rule must be a mapping of keys to values.")

    invalid_keys = set(rule) - VALID_TOP_LEVEL_KEYS
    if invalid_keys:
        raise RuleValidationError(
            f"Rule {rule.get('id', '<unknown>')} contains invalid keys: {sorted(invalid_keys)}."
        )

    if "id" not in rule or not isinstance(rule["id"], str) or not rule["id"].strip():
        raise RuleValidationError("Rule must include a non-empty 'id' string.")

    if "conditions" not in rule:
        raise RuleValidationError(f"Rule '{rule['id']}' is missing required key 'conditions'.")
    if "actions" not in rule:
        raise RuleValidationError(f"Rule '{rule['id']}' is missing required key 'actions'.")

    if not isinstance(rule["conditions"], dict):
        raise RuleValidationError(f"Rule '{rule['id']}': 'conditions' must be a mapping.")
    if not isinstance(rule["actions"], list):
        raise RuleValidationError(f"Rule '{rule['id']}': 'actions' must be a list.")

    if "description" in rule and rule["description"] is not None and not isinstance(rule["description"], str):
        raise RuleValidationError(f"Rule '{rule['id']}': 'description' must be a string.")
    if "metadata" in rule and rule["metadata"] is not None and not isinstance(rule["metadata"], dict):
        raise RuleValidationError(f"Rule '{rule['id']}': 'metadata' must be a mapping.")

    _validate_condition(rule["id"], rule["conditions"])
    for idx, action in enumerate(rule["actions"], start=1):
        _validate_action(rule["id"], idx, action)


def _validate_condition(rule_id: str, condition: Any) -> None:
    if not isinstance(condition, dict):
        raise RuleValidationError(f"Rule '{rule_id}': condition must be a mapping.")

    if "all_of" in condition or "any_of" in condition:
        if "all_of" in condition and "any_of" in condition:
            raise RuleValidationError(
                f"Rule '{rule_id}': condition may not contain both 'all_of' and 'any_of'."
            )

        operator_key = "all_of" if "all_of" in condition else "any_of"
        sub_conditions = condition[operator_key]
        if not isinstance(sub_conditions, list) or not sub_conditions:
            raise RuleValidationError(f"Rule '{rule_id}': '{operator_key}' must be a non-empty list.")

        invalid_keys = set(condition) - {operator_key}
        if invalid_keys:
            raise RuleValidationError(
                f"Rule '{rule_id}': invalid condition keys {sorted(invalid_keys)} in {operator_key}."
            )

        for sub_condition in sub_conditions:
            _validate_condition(rule_id, sub_condition)
        return

    if "not" in condition:
        if len(condition) != 1:
            invalid_keys = set(condition) - {"not"}
            raise RuleValidationError(
                f"Rule '{rule_id}': 'not' may not be combined with other condition keys: {sorted(invalid_keys)}."
            )
        _validate_condition(rule_id, condition["not"])
        return

    if not {"field", "operator", "value"}.issubset(condition):
        missing = {"field", "operator", "value"} - set(condition)
        raise RuleValidationError(
            f"Rule '{rule_id}': condition is missing keys {sorted(missing)}."
        )

    invalid_keys = set(condition) - VALID_CONDITION_KEYS
    if invalid_keys:
        raise RuleValidationError(
            f"Rule '{rule_id}': invalid condition keys {sorted(invalid_keys)}."
        )

    if not isinstance(condition["field"], str) or not condition["field"].strip():
        raise RuleValidationError(f"Rule '{rule_id}': 'field' must be a non-empty string.")

    if not isinstance(condition["operator"], str) or condition["operator"] not in VALID_OPERATORS:
        raise RuleValidationError(
            f"Rule '{rule_id}': 'operator' must be one of {sorted(VALID_OPERATORS)}."
        )


def _validate_action(rule_id: str, index: int, action: Any) -> None:
    if not isinstance(action, dict):
        raise RuleValidationError(f"Rule '{rule_id}': action at index {index} must be a mapping.")

    invalid_keys = set(action) - VALID_ACTION_KEYS
    if invalid_keys:
        raise RuleValidationError(
            f"Rule '{rule_id}': action at index {index} contains invalid keys: {sorted(invalid_keys)}."
        )

    if "type" not in action or not isinstance(action["type"], str) or not action["type"].strip():
        raise RuleValidationError(
            f"Rule '{rule_id}': action at index {index} must contain a non-empty 'type'."
        )

    if "parameters" in action and action["parameters"] is not None and not isinstance(action["parameters"], dict):
        raise RuleValidationError(
            f"Rule '{rule_id}': action '{action['type']}' parameters must be a mapping."
        )

    if "target" in action and action["target"] is not None and not isinstance(action["target"], str):
        raise RuleValidationError(
            f"Rule '{rule_id}': action '{action['type']}' target must be a string."
        )

    if "message" in action and action["message"] is not None and not isinstance(action["message"], str):
        raise RuleValidationError(
            f"Rule '{rule_id}': action '{action['type']}' message must be a string."
        )
