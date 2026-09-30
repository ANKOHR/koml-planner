import copy
import pytest
import yaml
from kpl.fixtures import SYNTHETIC_GOALS
from kpl.parse import select_template
from kpl.templates import TemplateLoadError, load_templates


@pytest.mark.parametrize('goal,expected', SYNTHETIC_GOALS)
def test_keyword_match_picks_expected_template(goal, expected):
    assert select_template(goal, load_templates())['name'] == expected


def test_priority_order_first_match_wins():
    templates = load_templates()
    assert select_template('research build outreach', list(reversed(templates)))['name'] == 'outreach'


def test_keyword_boundaries_and_case():
    assert select_template('BUILD a tool', load_templates())['name'] == 'build'
    assert select_template('rebuild buildings leadership', load_templates())['name'] == 'generic'


def test_catalogue():
    templates = load_templates()
    assert [t['name'] for t in templates] == ['outreach','build','research','writing','ops','generic']
    assert all(t['packages'] for t in templates)


@pytest.mark.parametrize('contents', ['name: [', '[]', 'name: test\npriority: bad', 'name: test\npriority: 1\nkeywords: []\npackages: []'])
def test_malformed_template_names_file(tmp_path, contents):
    (tmp_path / 'broken.yaml').write_text(contents)
    with pytest.raises(TemplateLoadError, match='broken.yaml'):
        load_templates(tmp_path)


def test_duplicate_priorities_rejected(tmp_path):
    templates = copy.deepcopy(load_templates())
    templates[1]['priority'] = templates[0]['priority']
    for t in templates:
        (tmp_path / (t['name']+'.yaml')).write_text(yaml.safe_dump(t))
    with pytest.raises(TemplateLoadError, match='duplicate'):
        load_templates(tmp_path)
