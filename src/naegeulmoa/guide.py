"""문체 수치 → AI 가 읽고 따라 쓰는 안내서(마크다운)."""
from __future__ import annotations

import random

from . import analyze, kinds

POLITE_YO = ('~잖아요', '~거든요', '~네요', '~는데요', '~고요', '~죠', '~예요/이에요', '~해요/어요/아요', '~세요', '~까요', '~요(기타)')
FOOTER = '\n---\n이 안내서는 **내글모아**로 만들었습니다 — 노드모아(https://nodemoa.com)가 만든 무료 도구.\n'


def tone(endings: dict) -> str:
    yo = sum(v for k, v in endings.items() if k in POLITE_YO)
    hapnida = endings.get('~습니다/ㅂ니다', 0)
    da = endings.get('~다(평서)', 0)
    ban = endings.get('~야/~지(반말)', 0)
    parts = sorted([('해요체(~요)', yo), ('합니다체(~습니다)', hapnida), ('~다 평서체', da), ('반말', ban)], key=lambda x: -x[1])
    main = [f'{n} {int(v*100)}%' for n, v in parts if v >= 0.05]
    return ' · '.join(main) or '섞어 씀'


def excerpt(body: str, n: int = 320) -> str:
    cut = body[:n]
    return cut + ('…' if len(body) > n else '')


def norms(kind: 'kinds.Kind') -> list[str]:
    """그 종류 글의 일반 규범 — 내 버릇과 부딪히면 규범을 먼저(예: 논문에 웃음 표시는 내 버릇이라도 빼기)."""
    out = [f'## 「{kind.name}」 쓸 때의 기본', *[f'- {n}' for n in kind.norms]]
    out += [f'- 꼭 넣을 것: {what}' for _, what in kind.must]
    return out


def build(profile_name: str, items: list[tuple[str, str, str, str]], m: dict,
          kind: 'kinds.Kind | None' = None, counts: dict | None = None) -> str:
    e = m['어미 비율']
    top_end = ', '.join(f'「{k}」 {int(v*100)}%' for k, v in list(e.items())[:6])
    p = m['1천 자당']
    habits = [f'{k} {v}' for k, v in p.items() if v >= 0.5 and k not in ('숫자',)]
    rare = [k for k, v in p.items() if v < 0.3 and k not in ('숫자', '영어 낱말')]
    titles = [t for _, t, _, _ in items if t][:6]
    first_lines = [b.split('\n', 1)[0][:50] for _, _, _, b in items][:6]
    last_lines = [[x for x in b.split('\n') if x.strip()][-1][:50] for _, _, _, b in items if b.strip()][:6]
    avoid = [w for w in analyze.AI_TELLS if w not in m['AI 티 나는 말']]
    chosen = random.Random(7).sample(items, min(3, len(items)))
    head = f'# 내 문체 안내서 — {profile_name}' + (f' · {kind.name}' if kind else ' · 전체')
    lines = [
        head,
        '',
        f'{"「" + kind.name + "」 " if kind else ""}글 {m["글 수"]}편({m["글자 수(공백 뺌)"]:,}자)에서 뽑았습니다. 글을 쓸 때 아래를 지키고, 끝나면 `check_draft` 로 견주어 고치세요.',
        '',
        '## 말투',
        f'- 주로: {tone(e)}',
        f'- 문장 끝: {top_end}',
        f'- 문장 길이 평균 {m["문장 길이 평균"]}자, 70자 넘는 긴 문장 {int(m["긴 문장(70자 이상) 비율"]*100)}%',
        f'- 자주 쓰는 부사 · 이음말: {", ".join(f"{k}({v})" for k, v in m["자주 쓰는 부사 · 이음말"].items()) or "뚜렷한 것 없음"}',
        f'- 문장을 자주 이렇게 엶: {", ".join(m["자주 여는 말(문장 첫 낱말)"][:8])}',
        '',
        '## 글 모양',
        f'- 글 길이 평균 {m["글 길이 평균"]:,}자, 문단 {m["문단 수 평균"]}개',
        f'- 줄 길이 평균 {m["줄 길이 평균"]}자, 20자 이하 짧은 줄 {int(m["짧은 줄(20자 이하) 비율"]*100)}%'
        + (' — 한 문장을 여러 줄로 끊어 씀' if m['짧은 줄(20자 이하) 비율'] >= 0.5 else ' — 문장을 이어서 씀'),
        f'- 버릇(1천 자당): {", ".join(habits) or "문장부호를 아껴 씀"}',
        f'- 거의 안 쓰는 것: {", ".join(rare) or "없음"}',
    ]
    if m['겹친 흉내말'] or m['한 글자 흉내말']:
        lines.append(f'- 흉내말: {", ".join(m["겹친 흉내말"][:8] + m["한 글자 흉내말"][:8])}')
    if titles:
        lines += ['', '## 제목 예', *[f'- {t}' for t in titles]]
    lines += ['', '## 글을 여는 첫 줄 예', *[f'- {t}' for t in first_lines]]
    lines += ['', '## 글을 맺는 끝 줄 예', *[f'- {t}' for t in last_lines]]
    if kind:
        lines += ['', *norms(kind)]
    elif counts:
        lines += ['', '## 종류별로 넣은 글', *[f'- {kinds.BY_ID[k].name if k in kinds.BY_ID else k}: {n}편' for k, n in counts.items()],
                  '- 블로그 · 공지처럼 종류가 정해진 글은 get_my_style_guide(kind=…) 로 그 종류 안내서를 읽으세요(종류마다 말투가 다릅니다).']
    lines += [
        '',
        '## 쓸 때 지킬 것',
        '- 위 수치와 예문의 말투 · 리듬 · 줄바꿈을 따른다. 규칙을 외우듯이 쓰지 말고, 예문을 소리 내어 읽었을 때와 같은 느낌으로.',
        '- 예문의 문장을 그대로 가져다 쓰지 않는다(옛 글과 겹치면 네이버 「유사 문서」 로 검색에서 밀릴 수 있음).',
        '- 사실(숫자 · 가격 · 날짜 · 제품 정보)은 사용자가 준 것만 쓴다. 모르면 비워 두고 묻는다.',
        '- 예문에 있는 오타 · 띄어쓰기 실수는 따라 하지 않고 바르게 쓴다.',
        f'- 이 사람이 거의 안 쓰는 AI 투 말은 피한다: {", ".join(a.replace("~", "") for a in avoid[:18])}',
        '',
        '## 예문(앞부분)',
    ]
    for sid, t, _, b in chosen:
        lines += ['', f'### {t or "글 " + sid}', '', '```', excerpt(b), '```']
    return '\n'.join(lines) + '\n' + FOOTER
