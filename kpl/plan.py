"""Expand literal template patterns into stable, topologically ordered packages."""
import json
from .parse import select_template
from .templates import load_templates


def create_plan(goal, templates=None):
    if not isinstance(goal, str) or not goal.strip():
        raise ValueError("SchemaError: goal must be a nonempty string")
    template = select_template(goal, load_templates() if templates is None else templates)
    skeletons = template["packages"]
    # Stable Kahn ordering. Cyclic skeletons remain in the output so validation
    # can report their actual package cycle, including a self-dependency.
    pending = list(skeletons)
    ordered = []
    seen = set()
    while pending:
        ready = next((p for p in pending if set(p["depends_on"]) <= seen), None)
        if ready is None:
            ordered.extend(pending)
            break
        ordered.append(ready)
        seen.add(ready["key"])
        pending.remove(ready)
    ids = {p["key"]: f"p{i}" for i, p in enumerate(ordered, 1)}
    return {"goal": goal, "template_used": template["name"], "packages": [
        {"id": ids[p["key"]], "title": p["title"].format(goal=goal),
         "task_type": template["name"], "depends_on": [ids[d] for d in p["depends_on"]],
         "estimate_hours": p["estimate_hours"], "acceptance": [a.format(goal=goal) for a in p["acceptance"]]}
        for p in ordered
    ]}


def plan_json(plan):
    return json.dumps(plan, indent=2, ensure_ascii=False, allow_nan=False) + "\n"
