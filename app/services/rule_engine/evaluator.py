from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation
from typing import Any


def _get_field_value(context: Any, field: str) -> Any:
    if isinstance(context, dict):
        if "." in field:
            parts = field.split(".")
            current: Any = context
            for part in parts:
                if not isinstance(current, dict) or part not in current:
                    return None
                current = current[part]
            return current
        return context.get(field)

    return getattr(context, field, None)


def _normalize_value(value: Any) -> Any:
    if isinstance(value, Decimal):
        return value
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return Decimal(str(value))
    if isinstance(value, str):
        try:
            return Decimal(value)
        except InvalidOperation:
            return value
    return value


def _numeric_range_match(actual: Any, range_values: Any) -> bool:
    if not isinstance(range_values, (list, tuple)) or len(range_values) != 2:
        return False

    lower, upper = range_values
    normalized_actual = _normalize_value(actual)
    normalized_lower = _normalize_value(lower)
    normalized_upper = _normalize_value(upper)

    if not isinstance(normalized_actual, Decimal):
        return False
    if not isinstance(normalized_lower, Decimal) or not isinstance(normalized_upper, Decimal):
        return False

    return normalized_lower <= normalized_actual <= normalized_upper


def _evaluate_comparison(field_value: Any, operator: str, condition_value: Any) -> bool:
    if operator == "equals":
        return field_value == condition_value

    if operator == "not_equals":
        return field_value != condition_value

    if operator in {"in", "not_in"}:
        target = condition_value
        if not isinstance(target, (list, tuple, set)):
            target = [target]

        if operator == "in" and len(target) == 2 and _numeric_range_match(field_value, target):
            return True

        result = field_value in target
        return result if operator == "in" else not result

    if operator in {"gt", "gte", "lt", "lte"}:
        try:
            if field_value is None:
                return False
            normalized_value = _normalize_value(field_value)
            normalized_condition = _normalize_value(condition_value)
            if not isinstance(normalized_value, Decimal) or not isinstance(normalized_condition, Decimal):
                return False

            if operator == "gt":
                return normalized_value > normalized_condition
            if operator == "gte":
                return normalized_value >= normalized_condition
            if operator == "lt":
                return normalized_value < normalized_condition
            return normalized_value <= normalized_condition
        except (TypeError, InvalidOperation):
            return False

    if operator == "contains":
        if field_value is None or condition_value is None:
            return False
        if isinstance(field_value, str) and isinstance(condition_value, str):
            return condition_value in field_value
        if isinstance(field_value, (list, tuple, set, dict)):
            return condition_value in field_value
        return False

    if operator == "matches":
        if field_value is None:
            return False
        try:
            return re.search(str(condition_value), str(field_value)) is not None
        except re.error:
            return False

    return False


def evaluate_condition(condition: dict[str, Any], context: Any) -> bool:
    if not isinstance(condition, dict):
        return False

    if "all_of" in condition:
        return all(evaluate_condition(sub, context) for sub in condition["all_of"])

    if "any_of" in condition:
        return any(evaluate_condition(sub, context) for sub in condition["any_of"])

    if "not" in condition:
        return not evaluate_condition(condition["not"], context)

    field = condition.get("field")
    operator = condition.get("operator")
    value = condition.get("value")

    if field is None or operator is None or "value" not in condition:
        return False

    field_value = _get_field_value(context, field)
    return _evaluate_comparison(field_value, operator, value)


def evaluate_rule(rule: dict[str, Any], context: Any) -> bool:
    return evaluate_condition(rule.get("conditions", {}), context)
