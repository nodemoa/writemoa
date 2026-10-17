"""내글모아 기본 시험 — examples/ 의 글(시험용으로 새로 쓴 글)과 짧은 견본으로 분석 · 종류 · 안내서 · 점검을 돌린다."""
import os, pathlib, tempfile
os.environ['NAEGEULMOA_HOME'] = tempfile.mkdtemp()
from naegeulmoa import analyze, guide, kinds, store

EX = pathlib.Path(__file__).parent.parent / 'examples'

PAPER = ('본 연구는 소규모 사업장의 전산 자산 관리 실태를 분석하였다. 선행 연구(김철수, 2021)에 따르면 자산대장을 갖춘 사업장은 '
         '전체의 31%에 그쳤다. 이에 본 연구는 수도권 사업장 120곳을 대상으로 설문을 실시하였다. 분석 결과 자산대장이 없는 사업장일수록 '
         '장비 교체 주기가 길었다. 따라서 자산대장 작성이 교체 계획 수립에 유의미한 영향을 미친다고 볼 수 있다.')
NOTICE = ('[공지] 사무실 이전 안내\n\n10월 28일(화)부터 사무실을 이전합니다.\n- 일시: 2026년 10월 28일 오전 9시부터\n- 장소: 서울시 ○○구 ○○로 12, 3층\n'
          '- 대상: 전 직원\n이전 당일에는 택배 접수가 어렵습니다. 협조 바랍니다.\n문의: 총무팀 02-123-4567')
EMAIL = ('김 과장님, 안녕하세요. 노드모아 박지은입니다.\n지난주 말씀드린 견적서를 첨부해 드립니다. 금액은 부가세 별도 기준이며, '
         '설치 일정은 다음 주 수요일로 잡아 두었습니다.\n검토하시고 금요일까지 회신 주시면 일정 확정하겠습니다.\n감사합니다.\n박지은 드림')
SNS = '오늘 첫 출근🌞\n떨리지만 설레는 하루!\n#첫출근 #새출발 #직장인'
REVIEW = ('다이소 실리콘 냄비받침 (2,000원)\n뜨거운 냄비 올려도\n식탁이 멀쩡하잖아요!\n말랑말랑한 실리콘이라 착 붙고\n설거지도 쓱 헹구면 끝.\n'
          '이 가격에 이 퀄리티라니 진짜 가성비 최고예요!\n장점은 튼튼함, 단점은 색이 하나뿐이라는 것 정도예요.')


def load():
    for p in sorted(EX.glob('*.txt')):
        title, _, body = store.read_sample(p)
        store.add_sample(body, title, '시험', 'blog-info')
    return store.samples('시험')


def test_sentences_join_lines():
    s = analyze.sentences('머리 감고 나서\n수건으로 말면\n툭 풀리잖아요.\n이건 쏙 끼우면 돼요!')
    assert s == ['머리 감고 나서 수건으로 말면 툭 풀리잖아요.', '이건 쏙 끼우면 돼요!']


def test_endings():
    assert analyze.ending_of('정말 편하잖아요ㅋㅋ') == '~잖아요'
    assert analyze.ending_of('오 분이면 충분합니다.') == '~습니다/ㅂ니다'


def test_detect_kinds():
    assert kinds.detect(PAPER)[0].id == 'paper'
    assert kinds.detect(NOTICE)[0].id == 'notice'
    assert kinds.detect(EMAIL)[0].id == 'email'
    assert kinds.detect(SNS)[0].id == 'sns'
    assert kinds.detect(REVIEW)[0].id == 'blog-review'
    assert kinds.detect((EX / '01.txt').read_text())[0].id == 'blog-info'


def test_norm_issues():
    assert any('느낌표' in m for m in kinds.norm_issues(kinds.BY_ID['paper'], PAPER + ' 정말 좋다!'))
    assert any('문의처' in m for m in kinds.norm_issues(kinds.BY_ID['notice'], '10월 28일 이전합니다. 협조 바랍니다.'))
    assert not kinds.norm_issues(kinds.BY_ID['notice'], NOTICE)


def test_profile_and_check():
    items = load()
    m = analyze.measure([b for *_, b in items])
    assert m['어미 비율'].get('~습니다/ㅂ니다', 0) > 0.6
    g = guide.build('시험', items, m, kind=kinds.BY_ID['blog-info'])
    assert '합니다체' in g and 'nodemoa.com' in g and '블로그(정보형)' in g
    store.save_profile({'전체': m, '종류별': {'blog-info': m}, '글 수': {'blog-info': 3}}, {'': g, 'blog-info': g}, '시험')
    yo = '오늘은 프린터 얘기예요!\n진짜 너무 편하잖아요ㅋㅋ\n다양한 기능을 효과적으로 알아보겠습니다~'
    tips = analyze.compare(analyze.measure([yo]), m)
    assert any('~습니다/ㅂ니다' in t for t in tips)
    assert any('AI 티' in t for t in tips)


def test_copied():
    items = store.samples('시험') or load()
    body = items[0][3]
    copied = analyze.copied_spans('새 글입니다.\n' + body.split('\n')[1], [b for *_, b in items])
    assert copied
