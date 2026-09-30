import json
from kpl.plan import create_plan
from kpl.render import executable_packages, render_packages, render_plan


def test_packages_lists_only_executable():
    plan = create_plan('build')
    assert [p['id'] for p in executable_packages(plan)] == ['p1']
    assert 'p2:' not in render_packages(plan)
    assert plan['packages'][0]['acceptance'][0] in render_packages(plan, 'md')
    assert '- [ ]' in render_packages(plan, 'md')


def test_render_text_shows_dependency_tree():
    text = render_plan(create_plan('build'))
    assert '\n  p2:' in text
    assert '\n    p3:' in text
    assert 'Template: build' in text
    assert 'depends on: p1' in text


def test_json_round_trip():
    plan = create_plan('write a guide')
    assert json.loads(render_plan(plan, 'json')) == plan


def test_diamond_graph_shows_all_dependencies():
    plan = create_plan('x')
    plan['packages'][2]['depends_on'] = ['p1']
    plan['packages'][3]['depends_on'] = ['p2', 'p3']
    text = render_plan(plan)
    assert 'depends on: p2, p3' in text
    assert '(shown above)' in text
