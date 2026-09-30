import pytest
import yaml
from kpl.plan import create_plan
from kpl.templates import load_templates
from kpl.validate import validate_plan


def test_validate_accepts_clean_plan():
    assert validate_plan(create_plan('build a tool')) == []


def test_validate_detects_cycle():
    plan = create_plan('build')
    plan['packages'][0]['depends_on'] = ['p2']
    assert 'CycleError: p1 -> p2 -> p1' in validate_plan(plan)


def test_validate_detects_dangling_dep():
    plan = create_plan('build')
    plan['packages'][0]['depends_on'] = ['absent']
    assert 'DanglingDepError: p1 -> absent' in validate_plan(plan)


def test_planted_cycle_and_dangling_reported_together():
    plan = create_plan('build')
    plan['packages'][0]['depends_on'] = ['p2', 'absent']
    errors = validate_plan(plan)
    assert any(e.startswith('CycleError:') for e in errors)
    assert any(e.startswith('DanglingDepError:') for e in errors)


def test_validate_rejects_missing_acceptance_criteria():
    plan = create_plan('x')
    plan['packages'][0]['acceptance'] = []
    assert 'MissingAcceptanceError: p1' in validate_plan(plan)


def test_validate_rejects_duplicate_ids():
    plan = create_plan('x')
    plan['packages'][1]['id'] = 'p1'
    assert 'DuplicateIdError: p1' in validate_plan(plan)


def test_negative_estimate():
    plan = create_plan('x')
    plan['packages'][0]['estimate_hours'] = -1
    assert 'NegativeEstimateError: p1' in validate_plan(plan)


@pytest.mark.parametrize('value', [None, [], {}, {'goal':'x'}, {'goal':'x','template_used':'generic','packages':[]}])
def test_not_a_plan_has_schema_error(value):
    assert validate_plan(value)[0].startswith('SchemaError:')


@pytest.mark.parametrize('value', [True, float('inf'), float('nan'), '1'])
def test_invalid_estimates(value):
    plan = create_plan('x')
    plan['packages'][0]['estimate_hours'] = value
    assert validate_plan(plan)[0].startswith('SchemaError:')


def test_template_yaml_self_dependency(tmp_path):
    templates = load_templates()
    templates[0]['packages'][0]['depends_on'] = ['scope']
    for t in templates:
        (tmp_path / (t['name'] + '.yaml')).write_text(yaml.safe_dump(t))
    plan = create_plan('outreach', load_templates(tmp_path))
    assert any(e.startswith('CycleError:') and e.endswith('p1 -> p1') for e in validate_plan(plan))
