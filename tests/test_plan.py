import time
import pytest
from kpl.fixtures import SYNTHETIC_GOALS
from kpl.plan import create_plan, plan_json
from kpl.templates import load_templates
from kpl.validate import validate_plan


@pytest.mark.parametrize('goal,expected', SYNTHETIC_GOALS)
def test_fixture_determinism_and_validation(goal, expected):
    plan = create_plan(goal)
    assert plan['template_used'] == expected
    assert not validate_plan(plan)
    assert plan_json(plan).encode() == plan_json(create_plan(goal)).encode()


def test_plan_packages_topologically_ordered():
    for template in load_templates():
        goal = template['keywords'][0] if template['keywords'] else 'something'
        seen = set()
        for package in create_plan(goal)['packages']:
            assert set(package['depends_on']) <= seen
            seen.add(package['id'])


def test_every_package_has_acceptance_criteria():
    for goal, _ in SYNTHETIC_GOALS:
        assert all(p['acceptance'] for p in create_plan(goal)['packages'])


def test_plan_records_template_used():
    assert create_plan('outreach build research')['template_used'] == 'outreach'


def test_unknown_goal_uses_generic_template():
    assert create_plan('x')['template_used'] == 'generic'


def test_long_goal_under_one_second():
    start = time.perf_counter()
    plan = create_plan('x' * 9994 + ' build')
    assert time.perf_counter() - start < 1
    assert plan['template_used'] == 'build'


def test_literal_goal_interpolation():
    goal = 'build {unknown} $value'
    assert goal in create_plan(goal)['packages'][0]['title']


def test_reorders_unsorted_skeletons():
    templates = load_templates()
    templates[0]['packages'].reverse()
    plan = create_plan('outreach', templates)
    assert not plan['packages'][0]['depends_on']
    assert not validate_plan(plan)


@pytest.mark.parametrize('goal', ['', '  ', None])
def test_invalid_goal(goal):
    with pytest.raises(ValueError, match='SchemaError'):
        create_plan(goal)
