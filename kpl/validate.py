"""Report named schema and dependency errors without executing packages."""
from .schema import SchemaError, check_schema


def validate_plan(plan):
    try:
        check_schema(plan)
    except SchemaError as exc:
        return [f"SchemaError: {exc}"]
    errors = []
    by_id = {}
    for package in plan["packages"]:
        identifier = package["id"]
        if identifier in by_id:
            errors.append(f"DuplicateIdError: {identifier}")
        by_id[identifier] = package
        if not package["acceptance"]:
            errors.append(f"MissingAcceptanceError: {identifier}")
        if package["estimate_hours"] < 0:
            errors.append(f"NegativeEstimateError: {identifier}")
    for package in plan["packages"]:
        for dep in package["depends_on"]:
            if dep not in by_id:
                errors.append(f"DanglingDepError: {package['id']} -> {dep}")
    # Iterative depth-first search avoids recursion limits on edited plans.
    state = {}
    for root in by_id:
        if state.get(root):
            continue
        path = [root]
        state[root] = 1
        stack = [iter(by_id[root]["depends_on"])]
        while stack:
            dep = next(stack[-1], None)
            if dep is None:
                state[path.pop()] = 2
                stack.pop()
            elif dep in by_id:
                if state.get(dep) == 1:
                    cycle = path[path.index(dep):] + [dep]
                    errors.append("CycleError: " + " -> ".join(cycle))
                elif not state.get(dep):
                    state[dep] = 1
                    path.append(dep)
                    stack.append(iter(by_id[dep]["depends_on"]))
    return errors
