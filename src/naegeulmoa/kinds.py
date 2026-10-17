"""글 종류 — 같은 사람도 블로그 · 논문 · 공지 · 업무 메일의 문체가 다르다.

종류마다 (1) 알아보는 신호, (2) 그 종류의 일반 규범(안내서에 붙임), (3) 점검 규칙을 둔다.
사람의 버릇은 종류마다 따로 재고, 그 종류 글이 없으면 「내 공통 버릇 + 그 종류 규범」 으로 쓴다.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from . import analyze


@dataclass
class Kind:
    id: str
    name: str
    about: str
    norms: list[str]
    must: list[tuple[str, str]] = field(default_factory=list)   # (정규식, 무엇) — 꼭 있어야 하는 것
    avoid: list[tuple[str, str]] = field(default_factory=list)  # (정규식, 있으면 할 말) — 있으면 안 되는 것


KINDS: list[Kind] = [
    Kind('blog-info', '블로그(정보형)', '정보 · 방법을 알려 주는 블로그 글',
         ['제목에 찾는 사람이 검색할 낱말을 넣는다.', '도입에서 독자의 상황에 공감한 뒤, 소제목별로 정보를 풀고, 끝에 정리한다.',
          '문단은 짧게, 사진 자리를 둔다. 끝에 해시태그 줄.'],
         avoid=[(r'\[\d+\]|et al\.|참고문헌', '논문식 인용 표시는 블로그에 어울리지 않습니다.')]),
    Kind('blog-review', '블로그(후기 · 리뷰형)', '제품 · 장소 · 서비스를 써 보고 쓴 후기',
         ['제품 이름 · 가격 같은 사실을 먼저 정확히.', '쓰기 전 불편 → 써 보니 → 좋은 점 · 아쉬운 점 → 누구에게 맞는지.',
          '느낌을 살리는 말(흉내말 · 감각어)을 쓰되 과장하지 않는다.', '대가를 받은 글이면 「광고」 · 「협찬」 을 맨 앞에 밝힌다(공정위 추천 · 보증 지침).'],
         must=[(r'\d[\d,]*\s*원|가격|무료', '가격(또는 무료) 정보')]),
    Kind('essay', '에세이 · 칼럼', '생각 · 경험을 풀어내는 글',
         ['「~다」 평서체가 기본.', '한 가지 생각을 끝까지 밀고 간다 — 경험 → 생각 → 여운.', '소제목보다 문단의 흐름으로.'],
         avoid=[(r'#\S+', '에세이에 해시태그는 어울리지 않습니다.')]),
    Kind('paper', '논문 · 보고서', '연구 · 분석 · 조사 결과를 쓰는 글',
         ['「~이다 · ~한다 · ~하였다」 학술 평서체.', '주장마다 근거와 출처(저자, 연도)를 붙인다.', '용어는 처음 나올 때 정의한다.',
          '서론 → 본론 → 결론, 1인칭 대신 「본 연구는」.', '감정 표현 · 구어 · 이모지 · 느낌표를 쓰지 않는다.'],
         avoid=[(r'!|ㅋ|ㅎㅎ|ㅜ|ㅠ|[\U0001F300-\U0001FAFF]', '논문 · 보고서에 느낌표 · 웃음 · 이모지가 있습니다.'),
                (r'진짜|완전|엄청|대박|되게|너무너무', '논문 · 보고서에 구어 강조어(진짜 · 완전 · 엄청 …)가 있습니다.'),
                (r'(해요|예요|에요|잖아요|거든요)[.!?]?\s*$', '논문 · 보고서에 「~요」 말투가 섞여 있습니다.')],
         must=[(r'\(\s*[^()]*\d{4}[^()]*\)|\[\d+\]|에 따르면', '근거 · 출처 표시(저자, 연도)')]),
    Kind('work-doc', '업무 문서(기획 · 보고 · 회의록)', '회사 안에서 쓰는 문서',
         ['개조식(~함 · ~임 · ~예정)과 번호 목록.', '결론 · 요청을 맨 앞에.', '날짜 · 담당 · 기한 · 수치(단위 포함)를 분명히.'],
         avoid=[(r'ㅋ|ㅎㅎ|ㅜ|ㅠ|[\U0001F300-\U0001FAFF]', '업무 문서에 웃음 · 이모지가 있습니다.')],
         must=[(r'\d{1,2}\s*[월/.]\s*\d{1,2}|\d{4}[-.]\d{1,2}|기한|까지', '날짜 · 기한')]),
    Kind('notice', '공지 · 안내문', '여러 사람에게 알리는 글',
         ['합니다체. 제목에 무엇을 알리는지 쓴다.', '필요한 항목(일시 · 장소 · 대상 · 내용 · 문의처)을 빠짐없이.', '바뀐 점은 눈에 띄게, 맺음은 「바랍니다 · 감사합니다」.'],
         must=[(r'\d{1,2}\s*[월/.]\s*\d{1,2}|\d{1,2}\s*시|일시|기간', '날짜 · 시간'),
               (r'문의|연락|전화|☎|@|\d{2,4}-\d{3,4}-\d{4}', '문의처')]),
    Kind('email', '업무 이메일 · 메시지', '사람에게 보내는 업무 연락',
         ['인사(○○님, 안녕하세요. ~입니다) → 용건 한 줄 → 자세한 내용 → 요청 · 기한 → 맺음(감사합니다. ~ 드림).', '존댓말, 첨부가 있으면 언급.'],
         must=[(r'안녕하|님[,\s]', '받는 사람 · 인사'), (r'감사|드림|올림|부탁드립니다', '맺음말')]),
    Kind('sns', 'SNS 짧은 글', '인스타 · 스레드 · 페이스북 같은 짧은 글',
         ['한두 줄에서 다섯 줄 안팎.', '첫 줄에서 눈길을 끈다.', '해시태그 · 이모지는 내 버릇만큼.'],
         avoid=[(r'^(?:[^\n]*\n){15,}', 'SNS 글로는 너무 깁니다.')]),
    Kind('lecture', '강의 · 설명글', '차근차근 가르치는 글',
         ['질문으로 열고 단계별로 설명한다.', '예시 · 비유로 쉽게, 어려운 용어는 풀어 쓴다.', '끝에 정리 · 퀴즈.'],
         must=[(r'예를 들|예시|처럼|비유', '예시 · 비유')]),
    Kind('press', '보도자료 · 홍보문', '언론 · 대외에 알리는 글',
         ['역피라미드: 누가 · 무엇을 · 언제를 첫 문단에.', '3인칭(「○○는 ~했다고 밝혔다」), 관계자 인용문.', '끝에 회사 소개. 과장 표현은 빼고 사실만.'],
         avoid=[(r'ㅋ|ㅎㅎ|ㅜ|ㅠ|!!', '보도자료에 웃음 · 겹느낌표가 있습니다.')]),
]
BY_ID = {k.id: k for k in KINDS}


def _flat(s: str) -> str:
    return re.sub(r'[\s·・ㆍ,_\-]', '', s).lower()


def find(kind: str) -> Kind | None:
    """아이디나 이름(일부)으로 종류 찾기 — 띄어쓰기 · 가운뎃점은 따지지 않는다(「후기·리뷰」 = 「후기 · 리뷰」)."""
    k = _flat(kind or '')
    if not k:
        return None
    for x in KINDS:
        if k == _flat(x.id):
            return x
    for x in KINDS:
        if k in _flat(x.name):
            return x
    return None


def signals(text: str) -> dict:
    sents = analyze.sentences(text)
    n = max(1, len(sents))
    lines = [ln.strip() for ln in text.split('\n') if ln.strip()]
    ends = [analyze.ending_of(s) for s in sents]
    gaejo = sum(1 for s in sents if re.search(r'(음|함|임|됨|있음|없음|필요|예정|완료|요망)[.]?$', analyze._TAIL.sub('', s)))
    return {
        '길이': len(re.sub(r'\s', '', text)),
        '줄 수': len(lines),
        '~다 비율': ends.count('~다(평서)') / n,
        '합니다 비율': ends.count('~습니다/ㅂ니다') / n,
        '요 비율': sum(1 for e in ends if e.startswith('~') and ('요' in e or e in ('~죠', '~세요'))) / n,
        '개조식 비율': gaejo / n,
        '목록 줄 비율': sum(1 for ln in lines if re.match(r'^([-•·*▶✔]|\d+[.)]|[①-⑳]|[가-하][.)])\s*', ln)) / max(1, len(lines)),
        '인용': len(re.findall(r'\(\s*[^()]*\d{4}[^()]*\)|\[\d+\]|et al\.|참고문헌|선행\s?연구|본 연구', text)),
        '해시태그': len(re.findall(r'#[^\s#]+', text)),
        '이모지': len(re.findall(r'[\U0001F300-\U0001FAFF☀-➿]', text)),
        '느낌표': text.count('!'),
        '웃음 · 울음': len(re.findall(r'ㅋ+|ㅎ{2,}|[ㅜㅠ]+', text)),
        '인사': bool(re.search(r'안녕하(세요|십니까)', text)),
        '맺음': bool(re.search(r'(드림|올림|감사합니다|부탁드립니다)[.!]?\s*$', text.strip()[-40:])),
        '공지 낱말': len(re.findall(r'일시|장소|대상|기간|신청|접수|문의|안내드립니다|바랍니다|공지', text)),
        '후기 낱말': len(re.findall(r'\d[\d,]*\s*원|가격|후기|리뷰|구매|가성비|장점|단점|추천|써 ?보니|내돈내산', text)),
        '강의 낱말': len(re.findall(r'볼까요|알아봅시다|예를 들|정리하면|퀴즈|단계|강좌|[①-⑳]|STEP', text)),
        '보도 낱말': len(re.findall(r'밝혔다|전했다|출시했다|발표했다|관계자|에 따르면|말했다', text)),
        '1인칭': len(re.findall(r'(^|\s)(나는|내가|나의|저는|제가)', text)),
        '받는 사람': bool(re.search(r'^\s*[^\s\n][^\n]{0,12}님\s*[,\n]', text)),
        '흉내말': len(re.findall(r'([가-힣]{2})\1', text)),
    }


def detect(text: str) -> tuple[Kind, list[str]]:
    """글 종류 짐작 — (종류, 그렇게 본 까닭)."""
    s = signals(text)
    sc: dict[str, float] = {k.id: 0.0 for k in KINDS}
    why: dict[str, list[str]] = {k.id: [] for k in KINDS}

    def add(kid: str, v: float, reason: str) -> None:
        if v:
            sc[kid] += v
            why[kid].append(reason)

    add('paper', 3 * min(s['인용'], 3), f'인용 표시 {s["인용"]}곳')
    add('paper', 2 if s['~다 비율'] > 0.6 and s['느낌표'] == 0 and s['요 비율'] < 0.05 else 0, '「~다」 평서 · 감정 표현 없음')
    add('essay', 2 if s['~다 비율'] > 0.5 and s['인용'] == 0 else 0, '「~다」 평서')
    add('essay', 1 if s['1인칭'] >= 2 and s['해시태그'] == 0 else 0, '1인칭으로 생각을 풂')
    add('work-doc', 4 * s['개조식 비율'] + 2 * s['목록 줄 비율'], f'개조식 {int(s["개조식 비율"]*100)}% · 목록 줄 {int(s["목록 줄 비율"]*100)}%')
    add('notice', 0.8 * min(s['공지 낱말'], 6), f'공지 낱말 {s["공지 낱말"]}개(일시 · 장소 · 문의 …)')
    add('email', (2 if s['받는 사람'] else 0) + (1.5 if s['맺음'] else 0) + (0.5 if s['인사'] else 0), '받는 사람 · 인사 · 맺음말')
    add('sns', 1.5 if s['길이'] < 280 and not (s['받는 사람'] or s['맺음'] or s['인사']) else 0, '인사 없이 짧은 글')
    add('sns', 0.5 * min(s['해시태그'], 6) + 0.3 * min(s['이모지'], 5), f'해시태그 {s["해시태그"]} · 이모지 {s["이모지"]}')
    add('blog-review', 0.7 * min(s['후기 낱말'], 8) + 0.3 * min(s['흉내말'], 5) + 0.15 * min(s['느낌표'], 10), f'후기 낱말 {s["후기 낱말"]} · 흉내말 {s["흉내말"]}')
    add('lecture', 0.8 * min(s['강의 낱말'], 6), f'설명 낱말 {s["강의 낱말"]}개(볼까요 · 예를 들어 · 정리 …)')
    add('press', 1.2 * min(s['보도 낱말'], 5), f'보도 낱말 {s["보도 낱말"]}개(밝혔다 · 관계자 …)')
    add('blog-info', 1.5 if s['인사'] and s['길이'] > 200 and not s['받는 사람'] else 0, '인사로 여는 글')
    add('blog-info', 1 if (s['합니다 비율'] + s['요 비율']) > 0.6 and s['길이'] > 200 and not s['받는 사람'] else 0, '존댓말로 풂')
    add('blog-info', 0.3 * min(s['해시태그'], 5) if s['길이'] > 400 else 0, '끝 해시태그')
    best = max(KINDS, key=lambda k: sc[k.id])
    if sc[best.id] < 1:
        best = BY_ID['blog-info']
        return best, ['뚜렷한 신호가 없어 블로그(정보형)로 봄']
    return best, why[best.id]


def norm_issues(kind: Kind, text: str) -> list[str]:
    """그 종류에 꼭 있어야 하는 것 · 없어야 하는 것."""
    out = []
    for pat, what in kind.must:
        if not re.search(pat, text, re.M):
            out.append(f'빠진 것: {what} — 「{kind.name}」 에 꼭 있어야 합니다.')
    for pat, msg in kind.avoid:
        if re.search(pat, text, re.M):
            out.append(msg)
    return out


def table() -> str:
    return '\n'.join(f'- {k.id} · {k.name}: {k.about}' for k in KINDS)
