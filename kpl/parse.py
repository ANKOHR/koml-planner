"""Case-insensitive literal keyword matching with whole-word boundaries."""
import re


def select_template(goal, templates):
    for template in sorted(templates, key=lambda t: t["priority"]):
        if template["name"] != "generic" and any(
            re.search(r"(?<!\w)" + re.escape(keyword) + r"(?!\w)", goal, re.IGNORECASE)
            for keyword in template["keywords"]
        ):
            return template
    return next(t for t in templates if t["name"] == "generic")
