"""내글모아 문체 분석 — 한국어 글에서 「그 사람 문체」를 숫자로 뽑고, 초안이 얼마나 닮았는지 잰다.

외부 형태소 분석기 없이 규칙만 쓴다(설치가 가볍고 결과를 설명하기 쉬움). 그만큼 한계가 있다:
명사로 끝나는 말이 반말처럼 보이기도 하고(「연어」), 그 반대도 있다. 수치는 「대략 이런 버릇」 으로 읽는다.
한국 블로그는 한 문장을 여러 줄로 끊어 쓰는 일이 많아, 줄을 이어 문장을 다시 만든 뒤에 어미를 본다.
"""
from __future__ import annotations

import collections
import re
import unicodedata

MAX_CHARS = 200_000  # 한 번에 받는 글 길이 상한(넘으면 앞부분만 씀) — 아주 긴 글로 멈추지 않게
_INVISIBLE = re.compile('[' + ''.join(map(chr, (0x200B, 0x200C, 0x2060, 0xFEFF, 0x00AD))) + ']')


def clean(text: str) -> str:
    """입력 다듬기 — 한글을 NFC 로(맥에서 복사한 글은 자모가 풀려 있기도 함), 줄바꿈은 \\n, 보이지 않는 글자는 뺀다."""
    t = unicodedata.normalize('NFC', text or '')
    t = re.sub(r'\r+\n', '\n', t).replace('\r', '\n')
    return _INVISIBLE.sub('', t)[:MAX_CHARS]


def is_emoji(ch: str) -> bool:
    o = ord(ch)
    return (0x1F000 <= o <= 0x1FAFF or 0x2600 <= o <= 0x27BF or 0x2B00 <= o <= 0x2BFF
            or o in (0xFE0F, 0x200D, 0x20E3))


def count_emoji(text: str) -> int:
    return sum(1 for ch in text if is_emoji(ch) and ord(ch) not in (0xFE0F, 0x200D, 0x20E3))


# 문장 끝에 붙는 꾸밈(문장부호 · 웃음 · 이모티콘) — 어미를 보기 전에 뗀다.
_DECO = set(' \t.!?…~;:^[]{}"\'`*-_<>=+,·ㅋㅎㅜㅠㅡ♡♥♪「」『』《》“”‘’')
_PAREN_END = re.compile(r'\([^()\n]{0,15}\)$|[:;]-?[()DPp]$')


def strip_tail(s: str) -> str:
    """「좋았어요(웃음)」 → 「좋았어요」, 「맛있어요😊」 → 「맛있어요」, 「좋아요 :)」 → 「좋아요」."""
    i = len(s)
    for _ in range(8):
        j = i
        while j and (s[j - 1] in _DECO or is_emoji(s[j - 1])):
            j -= 1
        m = _PAREN_END.search(s, max(0, j - 20), j)
        if m:
            j = m.start()
        if j == i:
            break
        i = j
    return s[:i]


def _jong(ch: str) -> int:
    """한글 음절의 받침 번호(없으면 0, 한글이 아니면 -1). ㄴ=4 · ㄹ=8 · ㅁ=16 · ㅂ=17."""
    o = ord(ch) - 0xAC00
    return o % 28 if 0 <= o < 11172 else -1


NOUN = '(명사 · 기타로 끝)'
# 해요체 끝말 — 위에서부터 먼저 맞는 것.
_YO = [('~잖아요', r'잖아요$'), ('~거든요', r'거든요$'), ('~더라고요', r'더라고요$'), ('~네요', r'네요$'), ('~군요', r'군요$'),
       ('~는데요', r'데요$'), ('~고요', r'고요$'), ('~예요/이에요', r'(예요|에요)$'), ('~세요', r'세요$'), ('~까요', r'까요$'),
       ('~나요', r'나요$'), ('~대요', r'(대요|래요)$')]
LEVEL = {name: '해요체' for name, _ in _YO}
LEVEL.update({'~어요/아요': '해요체', '~죠': '해요체', '~습니다/ㅂ니다': '합니다체', '~다(평서)': '~다 평서체',
              '~어/~지(반말)': '반말', '~음 · ~함(개조식)': '개조식', '~필요 · 예정(개조식)': '개조식', NOUN: '명사로 끝'})
# 해요체 가운데 사람마다 뚜렷이 갈리는 끝말(비교에 씀). 「~어요/아요」 는 해요체 전체라 따로 비교하지 않는다.
DISTINCT_ENDINGS = ('~잖아요', '~거든요', '~더라고요', '~네요', '~군요', '~는데요', '~고요', '~죠', '~나요', '~까요')
_BANMAL_STRONG = re.compile(r'(거든|더라|잖아|구나|구먼|려나|니까|냐|네|야|지)$')
_BANMAL_WEAK = re.compile(r'(던데|는데|은데|인데|해|봐|줘|돼|워|와|져|어|아|걸)$')
_GAEJO = re.compile(r'(있음|없음|음|함|임|됨|짐|봄|옴|줌|씀|냄|둠)$')
_GAEJO_NOUN = re.compile(r'(필요|중요|예정|완료|요망|불가|진행 ?중)$')


def ending_of(sentence: str) -> str:
    core = strip_tail(sentence)
    if not core:
        return NOUN
    if _GAEJO_NOUN.search(core):  # 「검토 필요」 — 「요」 로 끝나도 해요체가 아니다
        return '~필요 · 예정(개조식)'
    last = core[-1]
    if last in '요죠':
        for name, pat in _YO:
            if re.search(pat, core):
                return name
        return '~어요/아요' if last == '요' else '~죠'
    if core.endswith('니다') or core.endswith('시오'):
        return '~습니다/ㅂ니다'
    if core.endswith('니까') and len(core) >= 3 and (core[-3] == '습' or _jong(core[-3]) == 17):
        return '~습니다/ㅂ니다'  # 맞습니까 · 갑니까
    if core.endswith('시다') and len(core) >= 3 and _jong(core[-3]) == 17:
        return '~습니다/ㅂ니다'  # 넘어갑시다
    if _GAEJO.search(core):
        return '~음 · ~함(개조식)'
    if last == '다':
        return '~다(평서)'
    if _BANMAL_STRONG.search(core) or _BANMAL_WEAK.search(core):
        return '~어/~지(반말)'
    if last == '까' and len(core) >= 2 and (core[-2] == '을' or _jong(core[-2]) == 8):
        return '~어/~지(반말)'  # 먹을까 · 갈까
    if last == '대' and len(core) >= 2 and (_jong(core[-2]) == 4 or core[-2] in '는래'):
        return '~어/~지(반말)'  # 온대 · 한대
    return NOUN


def level_of(sentence: str) -> str:
    return LEVEL[ending_of(sentence)]


_LIST = re.compile(r'^\s*(?:[-•·*▶▷✔✓☞]\s*|\d{1,2}[.)]\s+|[①-⑳]\s*|[가-하][.)]\s+)')
_HEADING = re.compile(r'^\s*#{1,6}\s')
_TAGS_ONLY = re.compile(r'^\s*(?:#[^\s#]+\s*)+$')
_SPLIT = re.compile(r'(?<=[^\d\s][.!?…])\s+|(?<=[.!?…][.!?…])\s+')


def _split(chunk: str) -> list[str]:
    return [p.strip() for p in _SPLIT.split(chunk) if p.strip()]


def _line_ends(line: str) -> bool:
    """줄 끝이 문장 끝인가 — 마침표 · 웃음 · 이모지, 또는 확실한 끝말. 「~는데 · ~어」 처럼 이어지기도 하는 말은 끝으로 보지 않는다."""
    if strip_tail(line) != line.rstrip():
        return True
    lv = level_of(line)
    if lv in ('해요체', '합니다체', '~다 평서체', '개조식'):
        return True
    return lv == '반말' and bool(_BANMAL_STRONG.search(line.rstrip()))


def sentences(text: str) -> list[str]:
    """문장 목록. 줄 끝이 문장 끝일 때만 끊고, 아니면 다음 줄과 잇는다. 목록 줄은 한 줄이 한 문장, 소제목 · 해시태그 줄은 뺀다."""
    out: list[str] = []
    cur = ''
    for line in clean(text).split('\n'):
        line = re.sub(r'[ \t]+', ' ', line).strip()
        if not line or _HEADING.match(line) or _TAGS_ONLY.match(line):
            if cur:
                out += _split(cur)
                cur = ''
            continue
        if _LIST.match(line):
            if cur:
                out += _split(cur)
                cur = ''
            out += _split(_LIST.sub('', line, count=1))
            continue
        cur = (cur + ' ' + line).strip()
        if _line_ends(line):
            out += _split(cur)
            cur = ''
    if cur:
        out += _split(cur)
    return [s for s in out if len(s) >= 2]


ONE_SYLLABLE_MIMETIC = ['쏙', '톡', '팡', '착', '콕', '확', '쭉', '꽉', '딱', '탁', '훅', '쫙', '싹', '뚝', '펑', '쑥', '쓱', '척', '툭', '쾅']
_DUP_ONE = set(ONE_SYLLABLE_MIMETIC + list('살솔술쿵콩폭꾹뽀통퐁반빙빵찰촉팔펄훨활휙획뱅콜꿀깡쨍똑꼭번둥'))
_DUP_STOP = {'하나', '그래', '정말', '진짜', '너무', '자꾸', '조금', '가끔', '여기', '거기', '저기', '이거', '그거', '저거',
             '다시', '우리', '나중', '오늘', '내일', '사람', '이제', '그냥', '아주'}
ADVERBS = ('진짜 정말 너무 완전 엄청 되게 딱 꼭 막상 사실 그래서 결국 그냥 제발 아예 무조건 은근 살짝 확실히 솔직히 특히 '
           '그러면 그런데 근데 하지만 그리고 물론 역시 이제 아무튼 어쨌든 일단 우선 혹시 좀 많이 아마 다시 바로 같이 그래도 '
           '게다가 오히려 즉 참 꽤 거의 전혀 계속 벌써 아직 이미 항상 늘 자주 가끔 원래 따로 함께 생각보다 그러니까 왜냐하면').split()
_ADV = set(ADVERBS)
_PARTICLE = re.compile(r'(은|는|도|로|만|이|가|요)$')

# AI 가 쓴 티가 나는 말(한국어 LLM 글에 흔함). 내 글에서 드문데 초안에 나오면 짚는다. (이름, 정규식)
AI_TELLS: list[tuple[str, str]] = [
    ('알아보겠습니다', r'알아보겠습니다|알아보도록 하겠습니다'), ('살펴보겠습니다', r'살펴보겠습니다|살펴보도록'),
    ('결론적으로', r'결론적으로'), ('요약하자면', r'요약하자면'), ('정리하자면', r'정리하자면'), ('다양한', r'다양한'),
    ('효과적', r'효과적'), ('중요합니다', r'중요합니다'), ('필수적', r'필수적'), ('뿐만 아니라', r'뿐만 아니라'),
    ('또한', r'또한'), ('이처럼', r'이처럼'), ('이를 통해', r'이를 통해'), ('핵심은', r'핵심은'),
    ('도움이 되셨으면', r'도움이 되(?:셨|길|었으면|시길)'), ('마무리하며 · 마치며', r'마무리하며|마치며'),
    ('살펴본 바와 같이', r'살펴본 바와 같이'), ('극대화', r'극대화'), ('최적화', r'최적화'), ('손쉽게', r'손쉽게'),
    ('원활한', r'원활한'), ('체계적', r'체계적'), ('한 단계 더', r'한 단계 더'), ('알차게', r'알차게'),
    ('함께 알아봐요', r'함께 알아|같이 알아'), ('시작해 볼까요', r'시작해 볼까요'), ('아래와 같이', r'아래와 같이|다음과 같이'),
    ('~하는 것이 좋습니다', r'것이 좋습니다'), ('무엇보다', r'무엇보다'), ('한눈에', r'한눈에'),
    ('놓치지 마세요', r'놓치지 마세요'), ('궁금하셨던', r'궁금하셨던'),
    ('첫째, 둘째,', r'(?:^|\n|[.!?] )\s*(?:첫째|둘째|셋째)\s*,'),
]
_AI_RE = [(n, re.compile(p)) for n, p in AI_TELLS]
# 과장된 홍보 말 — 체험단 · 광고 글에 흔하다. 내 글에서 드문데 초안에 나오면 짚는다.
HYPE: list[tuple[str, str]] = [
    ('강력 추천 · 강추', r'강력 ?추천|강추'), ('가성비 최고 · 뛰어남', r'가성비[가는]?\s?(?:정말\s|진짜\s)?(?:최고|뛰어|갑|甲)|갓성비'),
    ('퀄리티 · 남다른', r'퀄리티|남다르|남달라'), ('후회하지 않을', r'후회하지 않|후회 없'), ('인생템 · 필수템', r'인생템|필수템|꿀템'),
    ('완벽한', r'완벽한|완벽하게'), ('최고의', r'최고의'), ('놀라운', r'놀라운|놀랍도록'), ('만족도 높은', r'만족도가?\s?(?:정말\s|매우\s|아주\s)?높'),
    ('모두 잡은', r'모두 잡은|다 잡은|두 마리 토끼'), ('힐링', r'힐링'), ('꼭 한번 가 보세요', r'꼭 한 ?번'),
]
_HYPE_RE = [(n, re.compile(p)) for n, p in HYPE]
CONTENT_ONLY = ('숫자', '영어 낱말')  # 내용에 따라 달라지는 것 — 문체로 보지 않음


def _per1k(n: float, chars: int) -> float:
    return round(n * 1000 / max(1, chars), 1)


def measure(texts: list[str]) -> dict:
    """글 여러 편(또는 한 편)의 문체 수치."""
    texts = [clean(t) for t in texts if t and t.strip()]
    allt = '\n'.join(texts)
    chars = len(re.sub(r'\s', '', allt))
    lines = [ln.strip() for t in texts for ln in t.split('\n') if ln.strip()]
    sents = [s for t in texts for s in sentences(t)]
    paras = [p for t in texts for p in re.split(r'\n\s*\n', t) if p.strip()]
    ll = [len(x) for x in lines]
    sl = [len(x) for x in sents]
    fine = collections.Counter(ending_of(s) for s in sents)
    lv = collections.Counter(LEVEL[k] for k in fine.elements())
    tot = sum(fine.values()) or 1
    no_num_range = re.sub(r'\d[\d:.,]*\s*[가-힣]{0,2}\s*~\s*\d', ' ', allt)  # 「10시~6시」 「3~5개」 의 물결은 버릇이 아님
    words = re.findall(r'[가-힣]+', allt)
    dup2 = collections.Counter(w for w in re.findall(r'([가-힣]{2})\1', allt) if w not in _DUP_STOP)
    dup1 = collections.Counter(w for w in re.findall(r'([가-힣])\1', allt) if w in _DUP_ONE)
    one = collections.Counter(w for w in words if w in ONE_SYLLABLE_MIMETIC)
    adv: collections.Counter = collections.Counter()
    for w in words:
        if w in _ADV:
            adv[w] += 1
        else:
            b = _PARTICLE.sub('', w)
            if b != w and b in _ADV:
                adv[b] += 1
    tells = {n: len(r.findall(allt)) for n, r in _AI_RE}
    hype = {n: len(r.findall(allt)) for n, r in _HYPE_RE}
    starts = collections.Counter(re.split(r'\s+', s)[0] for s in sents if s)
    return {
        '글 수': len(texts),
        '글자 수(공백 뺌)': chars,
        '문장 수': len(sents),
        '글 길이 평균': round(chars / max(1, len(texts))),
        '줄 길이 평균': round(sum(ll) / max(1, len(ll)), 1),
        '짧은 줄(20자 이하) 비율': round(sum(1 for x in ll if x <= 20) / max(1, len(ll)), 2),
        '문단 수 평균': round(len(paras) / max(1, len(texts)), 1),
        '문장 길이 평균': round(sum(sl) / max(1, len(sl)), 1),
        '긴 문장(70자 이상) 비율': round(sum(1 for x in sl if x >= 70) / max(1, len(sl)), 2),
        '말투 비율': {k: round(v / tot, 2) for k, v in lv.most_common()},
        '어미 비율': {k: round(v / tot, 2) for k, v in fine.most_common()},
        '1000자당': {
            '느낌표 !': _per1k(allt.count('!'), chars), '물음표 ?': _per1k(allt.count('?'), chars),
            '말줄임 …': _per1k(len(re.findall(r'\.\.+|…', allt)), chars), '물결 ~': _per1k(no_num_range.count('~'), chars),
            'ㅋ 웃음': _per1k(len(re.findall(r'ㅋ+', allt)), chars), 'ㅎ 웃음': _per1k(len(re.findall(r'ㅎ{2,}', allt)), chars),
            'ㅜ · ㅠ': _per1k(len(re.findall(r'[ㅜㅠ]+', allt)), chars),
            '따옴표': _per1k(len(re.findall(r'["“”\'‘’「」]', allt)) / 2, chars),
            '쉼표 ,': _per1k(len(re.findall(r'(?<!\d),|,(?!\d)', allt)), chars),
            '이모지': _per1k(count_emoji(allt), chars),
            '해시태그 #': _per1k(len(re.findall(r'(?<![#\w])#[^\s#]+', allt)), chars),
            '마크다운(**굵게** · ## 제목)': _per1k(len(re.findall(r'\*\*[^*\n]{1,80}\*\*|^#{1,6}\s', allt, re.M)), chars),
            '독자 부르기(여러분 · 이웃님)': _per1k(len(re.findall(r'여러분|이웃님|구독자님|독자님|님들', allt)), chars),
            '「저 · 제가」': _per1k(len(re.findall(r'(?<![가-힣])(?:저는|제가|저도|저를|저한테|저희)', allt)), chars),
            '「나 · 내가」': _per1k(len(re.findall(r'(?<![가-힣])(?:나는|내가|나도|나를|나한테)', allt)), chars),
            '숫자': _per1k(len(re.findall(r'\d+', allt)), chars), '영어 낱말': _per1k(len(re.findall(r'[A-Za-z]{2,}', allt)), chars),
        },
        '돈 표기': {'한글 단위(3만 원)': len(re.findall(r'\d+\s?[만천억]\s?원', allt)),
                  '숫자 쉼표(30,000원)': len(re.findall(r'\d{1,3}(?:,\d{3})+\s?원', allt))},
        '흉내말': [w for w, _ in (dup2 + collections.Counter({k + k: v for k, v in dup1.items()}) + one).most_common(12)],
        '자주 쓰는 부사 · 이음말': dict(adv.most_common(15)),
        '자주 여는 말(문장 첫 낱말)': [w for w, _ in starts.most_common(12)],
        'AI 티 나는 말': {n: c for n, c in tells.items() if c},
        '과장된 말': {n: c for n, c in hype.items() if c},
    }


def shingles(text: str, n: int = 12) -> set[str]:
    t = re.sub(r'\s+', '', text)
    return {t[i:i + n] for i in range(max(0, len(t) - n + 1))}


_POOL: dict[tuple, set[int]] = {}


def _pool(samples: list[str], n: int) -> set[int]:
    """옛 글 조각 모음. 여러 편에 되풀이되는 조각(늘 쓰는 인사 · 맺음말)은 빼서, 그것을 따라 써도 「베낌」 으로 보지 않는다."""
    key = (n, tuple(hash(s) for s in samples))
    if key not in _POOL:
        seen: collections.Counter = collections.Counter()
        for s in samples:
            seen.update({hash(x) for x in shingles(s, n)})
        _POOL.clear()
        _POOL[key] = {h for h, c in seen.items() if c == 1 or len(samples) == 1}
    return _POOL[key]


def copied_spans(draft: str, samples: list[str], n: int = 12, min_len: int = 15) -> tuple[list[str], float]:
    """초안 가운데 내 옛 글과 똑같은 문장, 그리고 겹친 비율(0~1). 옛 글을 그대로 옮기면 검색에서 중복 글로 보일 수 있다."""
    pool = _pool(samples, n)
    hits: list[str] = []
    total = same = 0
    for s in sentences(draft):
        flat = re.sub(r'\s+', '', s)
        if len(flat) < n:
            continue
        hs = [hash(flat[i:i + n]) for i in range(len(flat) - n + 1)]
        k = sum(1 for h in hs if h in pool)
        total += len(hs)
        same += k
        if len(flat) >= min_len and k >= max(1, len(hs) // 3):
            hits.append(s[:80])
    return hits, (same / total if total else 0.0)


def tone(levels: dict) -> str:
    parts = [f'{k} {int(v * 100)}%' for k, v in levels.items() if v >= 0.05 and k != '명사로 끝']
    return ' · '.join(parts) or '섞어 씀'


def compare(draft: dict, mine: dict, mode: str = 'same', free: tuple[str, ...] = ()) -> list[str]:
    """초안 수치를 내 문체와 견주어 고칠 점을 쉬운 말로. 한두 번 차이로는 짚지 않는다(초안이 짧으면 우연이 크다).

    mode — 'same': 같은 종류 내 글과 견줌(전부 봄).
           'family': 같은 갈래(블로그 · 후기 · SNS 처럼 편한 글)와 견줌 — 말투 · 낱말 · 문장부호는 보고, 길이 · 줄바꿈 · 문단은 종류마다 달라 뺌.
           'loose': 다른 종류 글과 견줌 — 내가 안 쓰는 버릇(문장부호 · 웃음 · AI 투 말 · 과장된 말)만 짚음.
    free: 그 종류에서 원래 쓰는 문장부호(보도자료의 따옴표, 강의의 물음표 …) — 짚지 않는다.
    """
    tips: list[str] = []
    dc = draft['글자 수(공백 뺌)']
    mc = max(1, mine['글자 수(공백 뺌)'])
    ns = draft['문장 수']
    same = mode == 'same'
    close = mode in ('same', 'family')

    def times(rate: float) -> float:  # 초안 길이에서 몇 번에 해당하나
        return rate * dc / 1000

    def near(a: float, b: float, rel: float, absol: float) -> bool:
        return abs(a - b) <= max(absol, abs(b) * rel)

    if same:
        for key, label, rel, ab in [('문장 길이 평균', '문장 길이', 0.25, 6), ('줄 길이 평균', '줄 길이', 0.25, 4)]:
            a, b = draft[key], mine[key]
            if ns >= 3 and not near(a, b, rel, ab):
                tips.append(f'{label}: 초안 평균 {a}자 · 내 글 {b}자 → ' + ('조금 더 길게' if a < b else '조금 더 짧게') + ' 쓰세요.')
        a, b = draft['글 길이 평균'], mine['글 길이 평균']
        if not near(a, b, 0.4, 200):
            tips.append(f'글 길이: 초안 {a:,}자 · 내 글 평균 {b:,}자(공백 뺌) → ' + ('내용을 더 채우세요.' if a < b else '줄이세요.'))
        if ns >= 3 and abs(draft['짧은 줄(20자 이하) 비율'] - mine['짧은 줄(20자 이하) 비율']) > 0.25:
            more = draft['짧은 줄(20자 이하) 비율'] < mine['짧은 줄(20자 이하) 비율']
            tips.append(f"줄바꿈: 짧은 줄이 초안 {int(draft['짧은 줄(20자 이하) 비율']*100)}% · 내 글 {int(mine['짧은 줄(20자 이하) 비율']*100)}% → "
                        + ('한 문장을 여러 줄로 나눠 쓰세요.' if more else '줄을 덜 나누고 이어 쓰세요.'))
        if mine['문단 수 평균'] >= 3 and draft['문단 수 평균'] < mine['문단 수 평균'] * 0.4 and dc >= 300:
            tips.append(f"문단: 내 글은 평균 {mine['문단 수 평균']}문단, 초안은 {draft['문단 수 평균']}문단 → 빈 줄로 문단을 더 나누세요.")
    if close and ns >= 4:
        dl, ml = draft['말투 비율'], mine['말투 비율']
        main = max((k for k in ml if k != '명사로 끝'), key=lambda k: ml[k], default=None)
        if main and ml[main] >= 0.4 and dl.get(main, 0) < ml[main] * 0.5 and (ml[main] - dl.get(main, 0)) * ns >= 2:
            tips.append(f'말투: 내 글은 {tone(ml)}, 초안은 {tone(dl)} → {main}로 맞추세요.')
        else:
            for k, a in dl.items():
                if k not in ('명사로 끝', main) and a >= 0.25 and ml.get(k, 0) < 0.05 and a * ns >= 2:
                    tips.append(f'말투: 초안에 {k}가 {int(a*100)}% — 내 글에서는 거의 안 씁니다.')
        de, me = draft['어미 비율'], mine['어미 비율']
        for k in DISTINCT_ENDINGS:
            a, b = de.get(k, 0), me.get(k, 0)
            if b >= 0.08 and b * ns >= 2 and a < b * 0.4:
                tips.append(f'끝말 「{k}」: 내 글 문장의 {int(b*100)}%가 이렇게 끝나는데 초안은 {int(a*100)}% → 어울리는 곳에서 더 쓰세요.')
            elif a >= 0.15 and a * ns >= 2 and a > b * 2.5 + 0.03:
                tips.append(f'끝말 「{k}」: 초안 {int(a*100)}% · 내 글 {int(b*100)}% → 줄이세요.')
    for k, a in draft['1000자당'].items():
        if k in CONTENT_ONLY or k in free:
            continue
        b = mine['1000자당'].get(k, 0)
        if b < 0.3 and a >= 1.0 and times(a) >= 1:
            tips.append(f'{k}: 내 글에서는 거의 안 쓰는데 초안에 {round(times(a))}번 → 빼세요.')
        elif close and b >= 1.0 and times(b) >= 2 and a < b * 0.35:
            tips.append(f'{k}: 내 글은 1,000자에 {b}번, 초안은 {a}번 → 조금 더 쓰세요.')
        elif b >= 1.0 and times(a) >= 2 and a > b * 2.5:
            tips.append(f'{k}: 초안 1,000자에 {a}번 · 내 글 {b}번 → 줄이세요.')
    if close:
        dadv = draft['자주 쓰는 부사 · 이음말']
        rate = {w: c * 1000 / mc for w, c in mine['자주 쓰는 부사 · 이음말'].items()}
        miss = [w for w, r in rate.items() if r >= 1.0 and r * dc / 1000 >= 1.5 and w not in dadv][:3]
        if miss:
            tips.append('내 글에 자주 나오는 말이 초안에 없음: ' + ', '.join(miss) + ' → 억지로 넣지 말고, 어울리는 자리가 있으면 쓰세요.')
        over = [f'{w}({c}번)' for w, c in dadv.items() if c >= 2 and c * 1000 / max(1, dc) > 2.5 * max(rate.get(w, 0), 0.5)]
        if over:
            tips.append('자주 쓰는 말을 몰아 넣은 느낌: ' + ', '.join(over) + ' — 내 글보다 훨씬 잦습니다. 줄이세요.')
    for key, label in (('AI 티 나는 말', 'AI 투 말'), ('과장된 말', '과장된 홍보 말')):
        hits = [f'{p}({c})' for p, c in draft[key].items() if mine.get(key, {}).get(p, 0) * dc / mc < c * 0.5]
        if hits:
            tips.append(f'{label}: ' + ', '.join(hits) + ' — 내 글에서는 드문 말입니다. 내 말로 바꾸세요.')
    return tips
