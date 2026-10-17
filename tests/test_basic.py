"""내글모아 기본 시험 — examples/ 의 글 세 편(시험용으로 새로 쓴 글)으로 분석 · 안내서 · 점검을 돌린다."""
import os, pathlib, tempfile
os.environ['NAEGEULMOA_HOME'] = tempfile.mkdtemp()
from naegeulmoa import analyze, guide, store

EX = pathlib.Path(__file__).parent.parent / 'examples'


def load():
    for p in sorted(EX.glob('*.txt')):
        title, body = store.read_sample(p)
        store.add_sample(body, title, '시험')
    return store.samples('시험')


def test_sentences_join_lines():
    s = analyze.sentences('머리 감고 나서\n수건으로 말면\n툭 풀리잖아요.\n이건 쏙 끼우면 돼요!')
    assert s == ['머리 감고 나서 수건으로 말면 툭 풀리잖아요.', '이건 쏙 끼우면 돼요!']


def test_endings():
    assert analyze.ending_of('정말 편하잖아요ㅋㅋ') == '~잖아요'
    assert analyze.ending_of('오 분이면 충분합니다.') == '~습니다/ㅂ니다'


def test_profile_and_check():
    items = load()
    m = analyze.measure([b for _, _, b in items])
    assert m['어미 비율'].get('~습니다/ㅂ니다', 0) > 0.6
    g = guide.build('시험', items, m)
    assert '합니다체' in g and 'nodemoa.com' in g
    store.save_profile(m, g, '시험')
    yo = '오늘은 프린터 얘기예요!\n진짜 너무 편하잖아요ㅋㅋ\n다양한 기능을 효과적으로 알아보겠습니다~'
    tips = analyze.compare(analyze.measure([yo]), m)
    assert any('~습니다/ㅂ니다' in t for t in tips)
    assert any('AI 티' in t for t in tips)


def test_copied():
    items = store.samples('시험') or load()
    body = items[0][2]
    copied = analyze.copied_spans('새 글입니다.\n' + body.split('\n')[1], [b for _, _, b in items])
    assert copied
