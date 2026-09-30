# KOML Planner

Say the goal. Get the graph. Every step checkable, every dependency explicit, no black box.

KOML Planner turns a goal sentence into a dependency graph of executable work packages using a deterministic, hand-written template library. It helps Henry turn an intention into a first checkable action before work starts. Python 3.10 or newer is required.

## Quickstart

With PyYAML, pytest and setuptools already installed, installation and use are entirely local:

```powershell
python -m pip install --no-index --no-deps --no-build-isolation -e .
python -m pytest -q
kpl plan --goal "ship a scoped paid trial for a warm lead" --out plan.json
kpl validate --plan plan.json
kpl render --plan plan.json --format text
kpl packages --plan plan.json --format md
```

The module invocation `python -m kpl.cli` supports the same arguments if the console command is not on PATH. No command makes network calls. No model, GPU workload, RNG or GPU package is used.

`plan` writes UTF-8 JSON with LF line endings and a final newline. Identical goal text and template library produce byte-identical files. Output contains no timestamps or random identifiers. `validate` prints zero errors on a clean plan and returns 0; invalid plans return 1 with named errors on stderr. `packages` lists only packages with an empty `depends_on` array, including their acceptance criteria. Dependencies refer to work that must be completed first. The schema has no completion state, so it cannot infer that a dependent package is ready after human work. Edit the plan or extend a downstream execution system to track completion.

`render --format text` prints an indented dependency tree with explicit dependency ids. Shared descendants appear under each parent; repeated nodes are marked `shown above` and their children are expanded once. `render --format json` emits the full plan. Reading commands validate before rendering or listing.

## Template catalogue and priority

The first matching template in this fixed priority order wins, even when several task types match. Keywords are literal, case-insensitive matches with whole-word boundaries, not unrestricted substrings within words. This follows the whole-word CLI specification: `build` matches `BUILD` but does not match `rebuild`. Punctuation forms a boundary; letters, digits and underscores do not. Literal keywords are escaped before matching, with no user-controlled regex.

| Priority | Template | Keywords | Work packages |
| --- | --- | --- | --- |
| 1 | outreach | outreach, contact, lead, pitch, email, prospects | Offer, recipients, messages, send, follow up |
| 2 | build | build, ship, implement, code, prototype, develop | Scope, design, implement, verify, deliver |
| 3 | research | research, investigate, compare, study | Questions, sources, analysis, conclusions |
| 4 | writing | write, draft, edit, article, essay, publish | Brief, outline, draft, revision |
| 5 | ops | ops, operations, organise, organize, maintain, backup, schedule | Procedure, resources, execution, review |
| 6 | generic | none; fallback on zero hits | Clarify outcome, identify action, act, review |

For example, `research build outreach` selects outreach exactly once. The demo selects outreach because `lead` outranks the build keyword `ship`. Each YAML file declares `name`, `keywords`, `priority`, and `packages`. Package skeletons declare `key`, `title`, `depends_on` keys, `estimate_hours`, and `acceptance`. Only `{goal}` interpolation is supported. Expansion orders acyclic skeletons topologically, preserving source order for ties, then assigns `p1`, `p2`, and so on. A template cycle is retained long enough for validation to name it; the CLI refuses to write an invalid plan.

## Plan JSON schema

The structural contract is enforced by `kpl/schema.py`:

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

Top-level goal and template_used must be nonempty strings; packages must be a nonempty array. Each package requires nonempty string id, title and task_type, string arrays depends_on and acceptance, and a finite numeric estimate_hours. Booleans are not numbers in this contract. Additional fields are tolerated for downstream tools. The example illustrates the schema; generated generic plans contain all four catalogue packages.

## Validation rules

| Named error | Condition |
| --- | --- |
| SchemaError | Invalid JSON or missing/incorrectly typed plan fields |
| DuplicateIdError | Two packages share an id |
| DanglingDepError | A dependency does not resolve to a package id |
| MissingAcceptanceError | A package has an empty acceptance array |
| NegativeEstimateError | An estimate is below zero |
| CycleError | A dependency cycle, including a self-dependency; lists ids in cycle order |
| TemplateLoadError | Malformed or invalid YAML library at startup, naming the file; library-wide errors name the directory |
| FileError | Input or output file cannot be accessed |

Blank acceptance entries are schema errors. A cycle plus a dangling dependency reports both named errors. Cycle detection uses an iterative depth-first traversal to avoid Python recursion limits. All subcommands load the template library at startup; malformed templates fail with a named error instead of a traceback.

## Architecture

```text
goal sentence
    |
    v
templates/*.yaml -> templates.py (load and check library)
    |                      |
    +----------------------v
                 parse.py (priority keyword selection)
                           |
                           v
                 plan.py (expand and order skeletons)
                           |
                           v
                 schema.py -> validate.py (check DAG)
                           |
                           v
               cli.py -> plan.json -> render.py
                                      |      |
                                      v      v
                                ready list  tree / JSON

fixtures.py (20 synthetic goals) -> tests/ (unit and CLI checks)
```

## HONESTY BOUNDARY

This planner is a scripted template matcher, explicitly not a language model and not an AI planner. Templates are hand-written. Keyword rules and their priority are documented above. Estimates are template defaults, not predictions of actual duration. Plans are starting scaffolds for a human to edit, not optimal decompositions. Every plan records `template_used`. Acceptance criteria are concrete template checks that still need human review for the specific goal. No claim is made that a language model generated these plans.

## Evidence and improvement hook

`kpl/fixtures.py` contains 20 labelled synthetic goals, not Henry's real past goals. The pytest suite checks all 20 expected labels, valid emitted graphs, nonempty acceptance, and identical output bytes across repeated planning. The required fixture threshold is 18/20; the library matches 20/20. Adversarial coverage includes three-template keyword stuffing, zero hits, a YAML self-dependency, a 10,000-character goal under one second, duplicate ids, a planted cycle plus a dangling dependency, and malformed inputs. CLI subprocess tests exercise every subcommand and rendering format.

The under-five-minute first-action hypothesis has not been measured on real users. Real trials are not shipped and no real-goal hit rate is claimed. After Henry runs 30 of his own past goals from his notes, record the count matched by keywords versus generic fallback and the resulting hit rate. Group fallback goals by observed pattern; add one template for the most common cluster, then re-run the same 30 goals. Keep it only if the measured hit rate improves. Record the sample date, matched counts before and after, percentage-point margin, observed cluster, new keywords and priority, and retain/remove decision here, without shipping private goal text. No measurement or improvement is fabricated in this build.

Verdict remains pending that trial: expand if real-goal hit rate clears 80%; integrate with koml-critic regardless so this fixed plan format can feed plan-then-attack; commercialise only as part of a larger ops offer; kill if Henry never runs it on real goals. Integration is a future consumer workflow, not an external call made by this CLI.

Deterministic scaffolds make pre-work reviewable, diffable and testable. KOML should prefer rule-based decomposition where templates cover the domain, and record the producing template for downstream critics and verifiers.

This repository is built and verified locally. Publication is handled separately.
