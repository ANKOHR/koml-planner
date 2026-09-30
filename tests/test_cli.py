import json
import os
from pathlib import Path
import subprocess
import sys
import pytest
from kpl.cli import main
from kpl.fixtures import SYNTHETIC_GOALS


def run(*args):
    return subprocess.run([sys.executable, '-m', 'kpl.cli', *map(str,args)], capture_output=True, text=True, timeout=10)


def test_cli_smoke_all_subcommands(tmp_path):
    path = tmp_path / 'plan.json'
    assert run('plan','--goal','ship a scoped paid trial for a warm lead','--out',path).returncode == 0
    assert run('validate','--plan',path).stdout.strip() == 'Valid plan: zero errors'
    for command, formats in [('packages',['text','md']),('render',['text','json'])]:
        for format in formats:
            result = run(command,'--plan',path,'--format',format)
            assert result.returncode == 0, result.stderr
            assert result.stdout
    assert json.loads(run('render','--plan',path,'--format','json').stdout)['template_used'] == 'outreach'


def test_determinism_byte_identical_plans(tmp_path):
    for goal, _ in SYNTHETIC_GOALS:
        first, second = tmp_path / 'a.json', tmp_path / 'b.json'
        assert main(['plan','--goal',goal,'--out',str(first)]) == 0
        assert main(['plan','--goal',goal,'--out',str(second)]) == 0
        assert first.read_bytes() == second.read_bytes()


@pytest.mark.parametrize('contents', ['not json','{}','[]'])
def test_cli_schema_error_without_traceback(tmp_path, contents):
    path = tmp_path / 'invalid.json'
    path.write_text(contents)
    result = run('validate','--plan',path)
    assert result.returncode == 1
    assert 'SchemaError:' in result.stderr
    assert 'Traceback' not in result.stderr


def test_cli_rejects_broken_plan(tmp_path):
    path = tmp_path / 'p.json'
    run('plan','--goal','build','--out',path)
    plan = json.loads(path.read_text())
    plan['packages'][0]['depends_on'] = ['p2','missing']
    path.write_text(json.dumps(plan))
    result = run('validate','--plan',path)
    assert result.returncode == 1
    assert 'CycleError: p1 -> p2 -> p1' in result.stderr
    assert 'DanglingDepError: p1 -> missing' in result.stderr


def test_cli_hand_edited_duplicate(tmp_path):
    path = tmp_path / 'p.json'
    run('plan','--goal','x','--out',path)
    plan = json.loads(path.read_text())
    plan['packages'][1]['id'] = 'p1'
    path.write_text(json.dumps(plan))
    assert 'DuplicateIdError: p1' in run('validate','--plan',path).stderr


def test_cli_missing_file(tmp_path):
    result = run('validate','--plan',tmp_path / 'absent.json')
    assert result.returncode == 1
    assert 'FileError:' in result.stderr


def test_cli_startup_template_error(monkeypatch, capsys):
    from kpl.templates import TemplateLoadError
    def fail():
        raise TemplateLoadError('broken.yaml: malformed YAML')
    monkeypatch.setattr('kpl.cli.load_templates', fail)
    assert main(['plan','--goal','x','--out','unused.json']) == 1
    assert 'TemplateLoadError: broken.yaml' in capsys.readouterr().err


def test_no_em_dash_in_shipped_files():
    root = Path(__file__).resolve().parents[1]
    files = list((root / 'kpl').rglob('*.py')) + list((root / 'kpl/templates').glob('*.yaml')) + list((root / 'tests').glob('*.py'))
    files += [root / 'README.md', root / 'pyproject.toml', root / '.gitignore']
    for path in files:
        assert chr(0x2014) not in path.read_text(encoding='utf-8'), str(path)
