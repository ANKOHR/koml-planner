"""Render dependency branches and packages ready to start."""
from .plan import plan_json


def executable_packages(plan):
    # The schema has no completion state: only dependency-free roots are ready.
    return [p for p in plan["packages"] if not p["depends_on"]]


def render_packages(plan, format="text"):
    lines = []
    for p in executable_packages(plan):
        lines.append(f"{'## ' if format == 'md' else ''}{p['id']}: {p['title']} ({p['estimate_hours']} h)")
        lines.extend(f"- [ ] {a}" if format == "md" else f"  Acceptance: {a}" for a in p["acceptance"])
    return "\n".join(lines) + "\n"


def render_plan(plan, format="text"):
    if format == "json":
        return plan_json(plan)
    lines = [f"Goal: {plan['goal']}", f"Template: {plan['template_used']}"]
    children = {p["id"]: [] for p in plan["packages"]}
    for p in plan["packages"]:
        for dep in p["depends_on"]:
            children[dep].append(p)
    stack = [(p, 0) for p in reversed(executable_packages(plan))]
    expanded = set()
    while stack:
        p, depth = stack.pop()
        repeated = p["id"] in expanded
        deps = ", ".join(p["depends_on"]) or "none"
        lines.append("  " * depth + f"{p['id']}: {p['title']} [depends on: {deps}]" + (" (shown above)" if repeated else ""))
        if not repeated:
            expanded.add(p["id"])
            stack.extend((child, depth + 1) for child in reversed(children[p["id"]]))
    return "\n".join(lines) + "\n"
