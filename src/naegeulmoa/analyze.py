"""내글모아 문체 분석 — 한국어 글에서 「그 사람 문체」를 숫자로 뽑고, 초안이 얼마나 닮았는지 잰다.

외부 형태소 분석기 없이 규칙만 쓴다(설치가 가볍고 결과를 설명하기 쉬움).
한국 블로그는 한 문장을 여러 줄로 끊어 쓰는 일이 많아, 줄을 이어 문장을 다시 만든 뒤에 어미를 본다.
"""
from __future__ import annotations

import collections
import re

# 문장 끝 어미 — 위에서부터 먼저 맞는 것으로 센다(긴 것부터).
ENDINGS: list[tuple[str, str]] = [
    ('~잖아요', r'잖아요$'), ('~거든요', r'거든요$'), ('~네요', r'네요$'), ('~는데요', r'(는데요|은데요|인데요)$'),
    ('~고요', r'고요$'), ('~죠', r'죠$'), ('~예요/이에요', r'(예요|에요)$'),
    ('~해요/어요/아요', r'(어요|아요|해요|워요|와요|져요|돼요|줘요|려요|겨요|녀요|봐요)$'),
    ('~세요', r'세요$'), ('~습니다/ㅂ니다', r'(습니다|니다)$'), ('~까요', r'까요$'), ('~요(기타)', r'요$'),
    ('~다(평서)', r'다$'), ('~야/~지(반말)', r'(야|지|어|아|해|네|군|자|래|냐|니)$'),
]
_TAIL = re.compile(r'[\s.!?…~ㅋㅎㅜㅠ;:^)\]"\'」』*]+$')
_END_LINE = re.compile(r'([.!?…~ㅋㅎㅜㅠ]|[요다죠네까])[\s.!?…~ㅋㅎㅜㅠ;^)"\'」』]*$')

ONE_SYLLABLE_MIMETIC = ['쏙', '톡', '팡', '착', '콕', '확', '쭉', '꽉', '딱', '탁', '훅', '쫙', '싹', '뚝', '펑', '쑥', '쓱', '척', '툭', '쾅']
ADVERBS = ('진짜 정말 너무 완전 엄청 되게 딱 꼭 막상 사실 그래서 결국 그냥 제발 아예 무조건 은근 살짝 확실히 솔직히 특히 '
           '그러면 그런데 하지만 그리고 물론 역시 이제 아무튼 어쨌든 일단 우선 혹시').split()

# AI 가 쓴 티가 나는 말(한국어 LLM 글에 흔함). 내 글에서 거의 안 쓰는데 초안에 자주 나오면 짚는다.
AI_TELLS = ['알아보겠습니다', '살펴보겠습니다', '결론적으로', '요약하자면', '다양한', '효과적으로', '효과적인', '중요합니다',
            '필수적', '뿐만 아니라', '또한', '이처럼', '이를 통해', '핵심은', '도움이 되셨', '도움이 되길', '마무리하며',
            '마치며', '정리하자면', '살펴본 바와 같이', '~에 대해', '극대화', '최적화', '손쉽게', '원활한', '체계적',
            '한 단계', '꿀팁', '알차게', '함께 알아', '시작해 볼까요', '그렇다면', '첫째', '둘째', '셋째']


def sentences(text: str) -> list[str]:
    """줄 끝이 문장 끝(마침표 · 요 · 다 · 죠 …)일 때만 끊고, 아니면 다음 줄과 잇는다."""
    out: list[str] = []
    cur = ''
    for line in text.split('\n'):
        line = re.sub(r'[ \t]+', ' ', line).strip()
        if not line:
            if cur:
                out.append(cur)
                cur = ''
            continue
        cur = (cur + ' ' + line).strip()
        if _END_LINE.search(line):
            out += [p.strip() for p in re.split(r'(?<=[.!?…])\s+', cur) if p.strip()]
            cur = ''
    if cur:
        out.append(cur)
    return [s for s in out if len(s) >= 2]


def ending_of(sentence: str) -> str:
    core = _TAIL.sub('', sentence)
    for name, pat in ENDINGS:
        if re.search(pat, core):
            return name
    return '(명사 · 기타로 끝)'


def _per1k(n: int, chars: int) -> float:
    return round(n * 1000 / max(1, chars), 1)


def measure(texts: list[str]) -> dict:
    """글 여러 편(또는 한 편)의 문체 수치."""
    texts = [t for t in texts if t.strip()]
    allt = '\n'.join(texts)
    chars = len(re.sub(r'\s', '', allt))
    lines = [ln.strip() for t in texts for ln in t.split('\n') if ln.strip()]
    sents = [s for t in texts for s in sentences(t)]
    paras = [p for t in texts for p in re.split(r'\n\s*\n', t) if p.strip()]
    ll = [len(x) for x in lines]
    sl = [len(x) for x in sents]
    ends = collections.Counter(ending_of(s) for s in sents)
    tot = sum(ends.values()) or 1
    dup = collections.Counter(re.findall(r'([가-힣]{2})\1', allt))
    one = collections.Counter(w for w in re.findall(r'[가-힣]+', allt) if w in ONE_SYLLABLE_MIMETIC)
    adv = collections.Counter(w for w in re.findall(r'[가-힣]+', allt) if w in ADVERBS)
    tells = {p: allt.count(p.replace('~', '')) for p in AI_TELLS if allt.count(p.replace('~', ''))}
    starts = collections.Counter(re.split(r'\s+', s)[0] for s in sents if s)
    return {
        '글 수': len(texts),
        '글자 수(공백 뺌)': chars,
        '글 길이 평균': round(chars / max(1, len(texts))),
        '줄 길이 평균': round(sum(ll) / max(1, len(ll)), 1),
        '짧은 줄(20자 이하) 비율': round(sum(1 for x in ll if x <= 20) / max(1, len(ll)), 2),
        '문단 수 평균': round(len(paras) / max(1, len(texts)), 1),
        '문장 길이 평균': round(sum(sl) / max(1, len(sl)), 1),
        '긴 문장(70자 이상) 비율': round(sum(1 for x in sl if x >= 70) / max(1, len(sl)), 2),
        '어미 비율': {k: round(v / tot, 2) for k, v in ends.most_common()},
        '1천 자당': {
            '느낌표 !': _per1k(allt.count('!'), chars), '물음표 ?': _per1k(allt.count('?'), chars),
            '말줄임 ..': _per1k(len(re.findall(r'\.\.+|…', allt)), chars), '물결 ~': _per1k(allt.count('~'), chars),
            'ㅋ 웃음': _per1k(len(re.findall(r'ㅋ+', allt)), chars), 'ㅎ 웃음': _per1k(len(re.findall(r'ㅎ{2,}', allt)), chars),
            'ㅜ · ㅠ': _per1k(len(re.findall(r'[ㅜㅠ]+', allt)), chars), '따옴표': _per1k(len(re.findall(r'["“”\'‘’「」]', allt)), chars),
            '쉼표 ,': _per1k(allt.count(','), chars), '이모지': _per1k(len(re.findall(r'[\U0001F300-\U0001FAFF☀-➿]', allt)), chars),
            '숫자': _per1k(len(re.findall(r'\d+', allt)), chars), '영어 낱말': _per1k(len(re.findall(r'[A-Za-z]{2,}', allt)), chars),
        },
        '겹친 흉내말': [a + a for a, _ in dup.most_common(12)],
        '한 글자 흉내말': [w for w, _ in one.most_common(12)],
        '자주 쓰는 부사 · 이음말': dict(adv.most_common(15)),
        '자주 여는 말(문장 첫 낱말)': [w for w, _ in starts.most_common(12)],
        'AI 티 나는 말': tells,
    }


def shingles(text: str, n: int = 14) -> set[str]:
    t = re.sub(r'\s+', '', text)
    return {t[i:i + n] for i in range(max(0, len(t) - n + 1))}


def copied_spans(draft: str, samples: list[str], n: int = 14, min_len: int = 22) -> list[str]:
    """초안 문장 가운데 내 옛 글과 글자째 겹치는 부분 — 그대로 베끼면 네이버 「유사 문서」 로 검색에서 밀릴 수 있다."""
    pool: set[str] = set()
    for s in samples:
        pool |= shingles(s, n)
    hits = []
    for s in sentences(draft):
        flat = re.sub(r'\s+', '', s)
        if len(flat) >= min_len and any(flat[i:i + n] in pool for i in range(len(flat) - n + 1)):
            hits.append(s[:80])
    return hits


def compare(draft: dict, mine: dict, same_kind: bool = True) -> list[str]:
    """초안 수치를 내 문체와 견주어, 고칠 점을 쉬운 말로.

    same_kind=False(그 종류 내 글이 없어 다른 종류 글과 견줄 때): 길이 · 줄바꿈 · 어미 · 「더 쓰세요」 는
    종류마다 다른 것이라 빼고, 내가 안 쓰는 버릇(문장부호 · 웃음 · AI 투 말)만 짚는다.
    """
    tips: list[str] = []

    def near(a: float, b: float, rel: float, absol: float) -> bool:
        return abs(a - b) <= max(absol, abs(b) * rel)

    for key, unit, rel, ab in ([('문장 길이 평균', '자', 0.2, 5), ('줄 길이 평균', '자', 0.2, 3), ('글 길이 평균', '자', 0.3, 150)] if same_kind else []):
        a, b = draft[key], mine[key]
        if not near(a, b, rel, ab):
            tips.append(f'{key}: 초안 {a}{unit} · 내 글 {b}{unit} → ' + ('더 길게' if a < b else '더 짧게') + ' 맞추세요.')
    if same_kind and abs(draft['짧은 줄(20자 이하) 비율'] - mine['짧은 줄(20자 이하) 비율']) > 0.2:
        tips.append(f"줄바꿈: 짧은 줄 비율 초안 {int(draft['짧은 줄(20자 이하) 비율']*100)}% · 내 글 {int(mine['짧은 줄(20자 이하) 비율']*100)}% → "
                    + ('한 문장을 여러 줄로 끊어 쓰세요.' if draft['짧은 줄(20자 이하) 비율'] < mine['짧은 줄(20자 이하) 비율'] else '줄을 덜 끊고 이어 쓰세요.'))
    de, me = draft['어미 비율'], mine['어미 비율']
    for k in (sorted(set(de) | set(me), key=lambda k: -me.get(k, 0)) if same_kind else []):
        a, b = de.get(k, 0), me.get(k, 0)
        if b >= 0.08 and a < b * 0.4:
            tips.append(f'어미 「{k}」: 내 글은 {int(b*100)}%인데 초안은 {int(a*100)}% → 더 쓰세요.')
        elif a >= 0.1 and a > b * 2.5 + 0.03:
            tips.append(f'어미 「{k}」: 초안 {int(a*100)}% · 내 글 {int(b*100)}% → 줄이세요.')
    for k, a in draft['1천 자당'].items():
        if k in ('숫자', '영어 낱말'):  # 내용에 따라 달라지는 것 — 문체로 보지 않음
            continue
        b = mine['1천 자당'].get(k, 0)
        if b < 0.3 and a >= 1.0:
            tips.append(f'{k}: 내 글에서는 거의 안 쓰는데 초안에 있음(1천 자당 {a}) → 빼세요.')
        elif same_kind and b >= 1.0 and a < b * 0.35:
            tips.append(f'{k}: 내 글은 1천 자당 {b}, 초안은 {a} → 조금 더 쓰세요.')
        elif b >= 1.0 and a > b * 2.5:
            tips.append(f'{k}: 초안 1천 자당 {a} · 내 글 {b} → 줄이세요.')
    used = set(draft['자주 쓰는 부사 · 이음말'])
    favorite = [w for w, c in mine['자주 쓰는 부사 · 이음말'].items() if c >= 2 and w not in used][:5]
    if favorite and same_kind:
        tips.append('내가 자주 쓰는 말이 초안에 없음: ' + ', '.join(favorite) + ' → 자연스러운 자리에 넣어 보세요.')
    for p, c in draft['AI 티 나는 말'].items():
        if mine['AI 티 나는 말'].get(p, 0) * (draft['글자 수(공백 뺌)'] / max(1, mine['글자 수(공백 뺌)'])) < c * 0.5:
            tips.append(f'AI 티: 「{p.replace("~", "")}」 {c}번 — 내 글에서는 드문 말입니다. 내 말로 바꾸세요.')
    return tips
