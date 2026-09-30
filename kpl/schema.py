"""Structural plan contract; graph rules live in validate.py."""
import math


class SchemaError(ValueError):
    pass


def check_schema(plan):
    def require(condition, message):
        if not condition:
            raise SchemaError(message)
    require(isinstance(plan, dict), "plan must be an object")
    for field in ("goal", "template_used"):
        require(isinstance(plan.get(field), str) and bool(plan[field].strip()), f"{field} must be a nonempty string")
    require(isinstance(plan.get("packages"), list) and bool(plan["packages"]), "packages must be a nonempty array")
    for index, package in enumerate(plan["packages"]):
        prefix = f"packages[{index}]"
        require(isinstance(package, dict), f"{prefix} must be an object")
        for field in ("id", "title", "task_type"):
            require(isinstance(package.get(field), str) and bool(package[field].strip()), f"{prefix}.{field} must be a nonempty string")
        for field in ("depends_on", "acceptance"):
            require(isinstance(package.get(field), list) and all(isinstance(v, str) and bool(v.strip()) for v in package[field]), f"{prefix}.{field} must be a string array")
        value = package.get("estimate_hours")
        require(type(value) in (int, float) and math.isfinite(value), f"{prefix}.estimate_hours must be a finite number")
