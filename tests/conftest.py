import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).parent / 'data'))
EX = pathlib.Path(__file__).parent.parent / 'examples'


@pytest.fixture(autouse=True)
def home(tmp_path, monkeypatch):
    """시험마다 빈 저장 폴더 — 시험끼리 서로 기대지 않게."""
    monkeypatch.setenv('NAEGEULMOA_HOME', str(tmp_path / 'home'))
    return tmp_path / 'home'


@pytest.fixture
def examples():
    from naegeulmoa import store
    out = []
    for p in sorted(EX.glob('*.txt')):
        title, _, body = store.read_sample(p)
        out.append((title, body))
    return out
