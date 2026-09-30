# KOML Planner

Say the goal. Get the graph. Every step checkable, every dependency explicit, no black box.

KOML Planner turns a vague goal into an ordered dependency graph of executable work packages using hand-written YAML templates. It runs locally on CPU, without network calls, model calls, randomness or GPU dependencies.

## Quickstart

Python 3.10 or later, PyYAML and pytest are required. With those dependencies and setuptools already available, install without network access:

```powershell
python -m pip install --no-index --no-build-isolation -e .
python -m pytest -q
kpl plan --goal "ship a scoped paid trial for a warm lead" --out plan.json
kpl validate --plan plan.json
kpl render --plan plan.json --format text
kpl packages --plan plan.json --format md
kpl render --plan plan.json --format json
```

The equivalent source-tree command is `python -m kpl.cli`. CLI errors go to stderr and return exit code 1; successful commands return 0. Argument errors return 2. The planner validates its output before writing it.

If a Windows user install warns that its Scripts directory is outside PATH, add the directory printed by pip to PATH, or use `python -m kpl.cli` immediately.

## Template catalogue and matching

| Priority | Template | Literal keywords |
| --- | --- | --- |
| 1 | outreach | outreach, contact, lead, pitch, email, prospects |
| 2 | build | build, ship, implement, code, prototype, develop |
| 3 | research | research, investigate, compare, study |
| 4 | writing | write, draft, edit, article, essay, publish |
| 5 | ops | ops, operations, organise, organize, maintain, backup, schedule |
| 6 | generic | fallback, no keywords |

Matching uses case-insensitive literal substring rules bounded by whole-word checks: a keyword cannot have a Unicode word character (letter, number or underscore) immediately before or after it. `BUILD` matches; `rebuild` does not. Keywords are escaped before regex matching. The first template by ascending priority with any hit wins, regardless of keyword position or number of hits. `research build outreach` selects outreach. No hits selects generic and always produces a nonempty plan.

Outreach covers offer, recipients, messages, sending and follow-up. Build covers scope, design, implementation, verification and delivery. Research covers questions, sources, analysis and conclusions. Writing covers brief, outline, draft and revision. Ops covers procedure, preparation, execution and review. Generic covers clarification, preparation, first action and review.

Each YAML file declares `name`, `keywords`, `priority` and `packages`. Skeletons declare a unique `key`, a `title` pattern, dependency keys, a default `estimate_hours` and acceptance patterns. `{goal}` expands literally to the supplied goal. Stable topological ordering assigns `p1`, `p2` and subsequent ids, then resolves dependency keys to those ids. Invalid files produce `TemplateLoadError` naming the file at CLI startup. Names and priorities must be unique, and exactly one generic template is required. Cyclic skeletons are preserved for graph validation to report `CycleError`.

## Plan JSON schema

```json
{
  "goal": "x",
  "template_used": "generic",
  "packages": [
    {
      "id": "p1",
      "title": "Clarify the outcome of x",
      "task_type": "generic",
      "depends_on": [],
      "estimate_hours": 0.5,
      "acceptance": ["An observable outcome, scope and constraints are written down."]
    }
  ]
}
```

`schema.py` enforces this structural contract. Top-level goal and template name are nonempty strings; packages is a nonempty array. Each package has nonempty id, title and task_type strings, string arrays for dependencies and acceptance, and a finite numeric estimate. Booleans are not estimates. Extra fields are permitted for downstream consumers such as koml-critic. JSON output is UTF-8, indented with two spaces and ends with a newline. Identical goal text with the same template library produces byte-identical output, without timestamps.

## Validation and rendering

`validate` checks structure and reports named errors without a traceback:

- `SchemaError`: invalid JSON or invalid plan structure.
- `DuplicateIdError`: repeated package id.
- `DanglingDepError`: dependency references an absent id, naming both ids.
- `MissingAcceptanceError`: empty acceptance list.
- `NegativeEstimateError`: estimate below zero.
- `CycleError`: directed cycle, listing ids including the repeated start id.

Graph checks collect errors, so a planted cycle and dangling dependency are reported together. Cycle detection is iterative to handle large hand-edited graphs. `FileError` covers unreadable files or failed output writes.

`packages` lists ready-to-start packages and their acceptance criteria as text or Markdown checkboxes. The schema has no completion state, so only packages with no dependencies are ready; merely having a dependency id present does not mean that work is complete. To advance readiness, a human must update the plan. `render --format text` shows an indented tree from roots to dependent work, labels every dependency and marks repeated nodes in shared branches. JSON rendering preserves the plan data. All commands validate a loaded plan before rendering it.

## Architecture

```text
goal -> parse.py keyword scan -> templates.py + templates/*.yaml
                                  |
                                  v
                              plan.py expansion
                                  |
                                  v
plan JSON -> schema.py -> validate.py -> render.py tree / packages / JSON
                 ^            ^
                 +-- cli.py --+
fixtures.py synthetic goals -> pytest component and CLI tests
```

## HONESTY BOUNDARY

This is a scripted template matcher, explicitly not a language model and not an AI planner. Templates are hand-written; matching uses literal keyword substring rules with whole-word boundaries in the documented priority order. Estimates are template defaults, not predictions of actual duration. Plans are starting scaffolds for a human to edit, not optimal decompositions. Every plan records `template_used`. No language model produces these plans. Acceptance criteria describe intended work; the planner does not execute that work or verify real-world completion.

## Evidence and improvement hook

The 20 labelled goals in `kpl/fixtures.py` are synthetic. Tests require 20/20 expected template selections, acceptance criteria on every emitted package, zero validation errors and deterministic output on every fixture. This exceeds the brief's 18/20 threshold but is evidence about the synthetic fixture only. The suite also covers keyword stuffing, generic fallback, YAML self-dependency, duplicate ids, a combined cycle and dangling reference, and a 10,000-character goal completing in under one second. This does not measure Henry's time to first action or real goal coverage.

The real-goal trial has not been run. After Henry supplies 30 past goals from his own notes, record keyword matches versus generic fallback and calculate `matched / 30`. Group fallback goals, write one template for the most common observed cluster, and remeasure the same goals. Record before and after counts and percentage-point margin here; retain the template only if the measured margin is positive. Trial results are recorded separately and not shipped as fixture data. No real trial results are claimed by this build.

After that measurement, expand the library if hit rate clears 80%; integrate with koml-critic regardless through this fixed plan format; commercialise only within a larger ops offer; kill if Henry never uses it on real goals. These are future decisions, not completed integrations. Deterministic scaffolds keep plans reviewable, diffable and testable, and template provenance gives a downstream critic a clear starting point.
