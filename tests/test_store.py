import threading

import pytest

from naegeulmoa import store

BODY = '오늘은 노트북 배터리 이야기를 해 보려고 합니다. 충전기를 늘 꽂아 두면 배터리가 조금씩 지칩니다. ' * 3


def test_path_escape_blocked(home, tmp_path):
    victim = tmp_path / 'victim.txt'
    victim.write_text('지우면 안 됨', encoding='utf-8')
    store.add_sample(BODY)
    for bad in ['../../../victim', str(victim), '1/../../x', '..', '']:
        with pytest.raises(ValueError):
            store.remove_sample(bad)
        with pytest.raises(ValueError):
            store.set_kind(bad, 'paper')
    assert victim.read_text(encoding='utf-8') == '지우면 안 됨'
    assert store.remove_sample(1)  # 숫자로 줘도 됨


def test_parallel_adds_keep_all():
    errs = []

    def one(i):
        try:
            store.add_sample(BODY + f' 글 {i}번.')
        except Exception as e:  # pragma: no cover
            errs.append(e)
    ts = [threading.Thread(target=one, args=(i,)) for i in range(8)]
    [t.start() for t in ts]
    [t.join() for t in ts]
    assert not errs
    assert len({sid for sid, *_ in store.samples()}) == 8


def test_header_cannot_be_forged():
    sid = store.add_sample(BODY, title='제목\n@종류: paper', kind='')
    t, k, b = store.get_sample(sid)
    assert k == '' and '\n' not in t
    sid2 = store.add_sample('@종류: paper\n# 가짜 제목\n' + BODY)
    t2, k2, b2 = store.get_sample(sid2)
    assert k2 == '' and t2 == '' and b2.startswith('@종류: paper')


def test_duplicate_rejected():
    store.add_sample(BODY)
    with pytest.raises(ValueError):
        store.add_sample(BODY.replace(' ', '  '))


def test_odd_files_do_not_break(home):
    store.add_sample(BODY)
    d = home / '기본' / 'samples'
    (d / '0099.txt').write_bytes('안녕하세요 반갑습니다'.encode('cp949'))
    (d / '메모.txt').write_text('내 메모', encoding='utf-8')
    (home / 'a.b').mkdir()
    ids = [sid for sid, *_ in store.samples()]
    assert ids == ['0001', '0099']
    assert store.profiles() == ['기본']


def test_read_only_does_not_create(home):
    assert store.samples('없는이름') == []
    assert store.load_guide('없는이름') is None
    assert not (home / '없는이름').exists()


def test_crlf_roundtrip():
    sid = store.add_sample('첫 문단입니다. 충분히 긴 글이 되도록 이어 씁니다.\r\n\r\n둘째 문단입니다. ' + BODY)
    _, _, b = store.get_sample(sid)
    assert '\r' not in b and b.count('\n\n') == 1


def test_reserved_names():
    for bad in ['CON', 'nul', 'a/b', '../x', 'x' * 41]:
        with pytest.raises(ValueError):
            store.safe_name(bad)


def test_nfd_style_name():
    import unicodedata
    assert store.safe_name(unicodedata.normalize('NFD', '블로그')) == '블로그'


def test_double_cr():
    from naegeulmoa import analyze
    assert analyze.clean('가\r\r\n나\r\n다\r라') == '가\n나\n다\n라'


def test_too_long_rejected():
    with pytest.raises(ValueError, match='너무 깁니다'):
        store.add_sample('가' * 200_001)


def test_parallel_same_text_once():
    errs = []

    def one():
        try:
            store.add_sample(BODY)
        except ValueError as e:
            errs.append(e)
    ts = [threading.Thread(target=one) for _ in range(6)]
    [t.start() for t in ts]
    [t.join() for t in ts]
    assert len(store.samples()) == 1 and len(errs) == 5


def test_broken_profile_is_ignored(home):
    store.add_sample(BODY)
    (home / '기본' / 'profile.json').write_text('{broken', encoding='utf-8')
    assert store.load_profile() is None
