"""The local-only kpl command-line interface."""
import argparse
import json
from pathlib import Path
import sys
from .plan import create_plan, plan_json
from .render import render_packages, render_plan
from .templates import TemplateLoadError, load_templates
from .validate import validate_plan


def main(argv=None):
    parser = argparse.ArgumentParser(description="Scripted hand-written templates, not an AI planner. Estimates are defaults.")
    commands = parser.add_subparsers(dest="command", required=True)
    planning = commands.add_parser("plan")
    planning.add_argument("--goal", required=True)
    planning.add_argument("--out", required=True, type=Path)
    for name in ("validate", "packages", "render"):
        command = commands.add_parser(name)
        command.add_argument("--plan", required=True, type=Path)
        if name != "validate":
            command.add_argument("--format", choices=("text", "md") if name == "packages" else ("text", "json"), default="text")
    args = parser.parse_args(argv)
    try:
        templates = load_templates()
        if args.command == "plan":
            plan = create_plan(args.goal, templates)
        else:
            try:
                plan = json.loads(args.plan.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, UnicodeError) as exc:
                raise ValueError(f"SchemaError: {args.plan}: invalid JSON ({exc})") from exc
        errors = validate_plan(plan)
        if errors:
            print("\n".join(errors), file=sys.stderr)
            return 1
        if args.command == "plan":
            args.out.write_bytes(plan_json(plan).encode("utf-8"))
            print(f"Wrote {args.out} (template: {plan['template_used']})")
        elif args.command == "validate":
            print("Valid plan: zero errors")
        elif args.command == "packages":
            print(render_packages(plan, args.format), end="")
        else:
            print(render_plan(plan, args.format), end="")
        return 0
    except (TemplateLoadError, ValueError, OSError) as exc:
        name = "TemplateLoadError" if isinstance(exc, TemplateLoadError) else "FileError" if isinstance(exc, OSError) else ""
        print(f"{name + ': ' if name else ''}{exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
