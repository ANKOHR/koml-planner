"""Load and check the hand-written template library."""
from pathlib import Path
import math
import yaml


class TemplateLoadError(ValueError):
    pass


def load_templates(directory=None):
    directory = Path(directory) if directory is not None else Path(__file__).with_name("templates")
    def require(condition, message):
        if not condition:
            raise ValueError(message)

    templates = []
    for path in sorted(directory.glob("*.yaml")):
        try:
            item = yaml.safe_load(path.read_text(encoding="utf-8"))
            require(isinstance(item, dict), "expected a mapping")
            require(isinstance(item.get("name"), str) and item["name"], "missing name")
            require(type(item.get("priority")) is int, "priority must be an integer")
            require(isinstance(item.get("keywords"), list), "keywords must be a list")
            require(all(isinstance(k, str) and k.strip() for k in item["keywords"]), "invalid keyword")
            packages = item.get("packages")
            require(isinstance(packages, list) and packages, "packages must be nonempty")
            keys = set()
            for package in packages:
                require(isinstance(package, dict), "package must be a mapping")
                key = package.get("key")
                require(isinstance(key, str) and key and key not in keys, "invalid or duplicate package key")
                keys.add(key)
                require(isinstance(package.get("title"), str) and package["title"].strip(), "missing title")
                require(isinstance(package.get("depends_on"), list), "missing dependencies")
                require(all(isinstance(d, str) for d in package["depends_on"]), "invalid dependency")
                value = package.get("estimate_hours")
                require(type(value) in (int, float) and math.isfinite(value) and value >= 0, "invalid estimate")
                require(isinstance(package.get("acceptance"), list) and package["acceptance"], "missing acceptance")
                require(all(isinstance(a, str) and a.strip() for a in package["acceptance"]), "invalid acceptance")
                for pattern in [package["title"], *package["acceptance"]]:
                    pattern.format(goal="example")
            require(all(d in keys for p in packages for d in p["depends_on"]), "unknown package key")
            templates.append(item)
        except (AttributeError, ValueError, TypeError, KeyError, IndexError, OSError, yaml.YAMLError) as exc:
            raise TemplateLoadError(f"{path.name}: {exc}") from exc
    if not templates or sum(t["name"] == "generic" for t in templates) != 1:
        raise TemplateLoadError(f"{directory}: exactly one generic template required")
    if len({t["name"] for t in templates}) != len(templates) or len({t["priority"] for t in templates}) != len(templates):
        raise TemplateLoadError(f"{directory}: duplicate template name or priority")
    return sorted(templates, key=lambda t: t["priority"])
