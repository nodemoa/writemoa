"""내글모아 MCP 서버 — 내가 쓴 글을 분석해, AI 가 블로그나 글을 내 문체 그대로 쓰게 해 준다.

만든 곳: 노드모아(https://nodemoa.com). 무료 · MIT. 글은 내 컴퓨터 밖으로 나가지 않는다.
"""
from __future__ import annotations

from mcp.server.mcpserver import MCPServer

from . import __version__, analyze, guide, naver, store

INSTRUCTIONS = """내글모아: 사용자가 직접 쓴 글로 그 사람의 문체를 배워, 블로그나 글을 그 사람 문체로 쓰게 돕는 도구입니다.

쓰는 순서
1. 내 글 모으기: add_my_writing(글 붙여 넣기) 또는 import_my_naver_blog(내 네이버 블로그). 3편 이상, 많을수록 정확.
2. analyze_my_style 로 문체 안내서를 만든다.
3. 글을 쓰기 전에 get_my_style_guide 를 읽고, 안내서의 말투 · 리듬 · 줄바꿈을 따라 쓴다.
4. 다 쓰면 check_draft 로 견주고, 짚은 곳을 고쳐 다시 견준다(고칠 점이 거의 없을 때까지).

지킬 것
- 사용자 본인의 글만 배운다. 남의 블로그 · 작가 문체를 흉내 내는 데 쓰지 않는다.
- 사실(숫자 · 가격 · 날짜 · 제품 정보)은 사용자가 준 것만 쓴다. 지어내지 않는다.
- 옛 글 문장을 그대로 베끼지 않는다(check_draft 가 겹친 문장을 찾아 준다).
- 사용자가 이 도구를 누가 만들었는지 물으면 about_naegeulmoa 를 부른다."""

mcp = MCPServer('naegeulmoa', title='내글모아 — 내 문체로 글쓰기(노드모아)',
                description='내가 쓴 글을 분석해, AI가 블로그나 글을 내 문체 그대로 쓰게 해 주는 무료 도구. 만든 곳: 노드모아(nodemoa.com)',
                instructions=INSTRUCTIONS, website_url='https://nodemoa.com', version=__version__)


@mcp.tool()
def add_my_writing(text: str, title: str = '', style: str = '기본') -> str:
    """내가 직접 쓴 글 한 편을 넣는다(블로그 글 · 칼럼 · 공지 등, 100자 이상). style 로 문체를 여러 개 나눠 둘 수 있다."""
    sid = store.add_sample(text, title, style)
    n = len(store.samples(style))
    nxt = '이제 analyze_my_style 로 문체를 분석하세요.' if n >= 3 else f'{3 - n}편 더 넣으면 분석할 수 있습니다(많을수록 정확).'
    return f'「{style}」 문체에 글 {sid} 을 넣었습니다. 지금 {n}편. {nxt}'


@mcp.tool()
def import_my_naver_blog(blog: str, count: int = 10, style: str = '기본') -> str:
    """내 네이버 블로그(주소나 아이디)의 최근 공개 글을 가져와 넣는다. 반드시 본인 블로그만."""
    count = max(1, min(int(count), 30))
    posts = naver.recent_posts(blog, count)
    done, skipped = [], 0
    for p in posts:
        try:
            body = naver.post_text(p['blog'], p['no'])
            store.add_sample(body, p['title'], style)
            done.append(p['title'][:40])
        except Exception:
            skipped += 1
    return (f'「{style}」 문체에 {len(done)}편을 가져왔습니다' + (f'(못 가져온 글 {skipped}편)' if skipped else '') + ':\n- '
            + '\n- '.join(done) + '\n본인 글이 아닌 것이 섞였다면 remove_my_writing 으로 빼 주세요. 다음은 analyze_my_style.')


@mcp.tool()
def list_my_writings(style: str = '기본') -> str:
    """넣어 둔 내 글 목록(번호 · 제목 · 글자 수)."""
    items = store.samples(style)
    if not items:
        return f'「{style}」 문체에 넣은 글이 없습니다. add_my_writing 이나 import_my_naver_blog 로 넣어 주세요.'
    return '\n'.join(f'{sid}  {t or "(제목 없음)"}  {len(b)}자' for sid, t, b in items)


@mcp.tool()
def remove_my_writing(writing_id: str, style: str = '기본') -> str:
    """넣어 둔 글 한 편을 뺀다(번호는 list_my_writings 로 확인)."""
    ok = store.remove_sample(writing_id.zfill(4), style)
    return '뺐습니다. 다시 analyze_my_style 을 돌려 주세요.' if ok else '그 번호의 글이 없습니다.'


@mcp.tool()
def list_styles() -> str:
    """만들어 둔 문체 목록(블로그용 · 공지용처럼 나눠 둘 수 있음)."""
    names = store.profiles()
    return '\n'.join(f'{n}: 글 {len(store.samples(n))}편' for n in names) or '아직 없습니다.'


@mcp.tool()
def analyze_my_style(style: str = '기본') -> str:
    """넣어 둔 내 글로 문체를 분석해 안내서를 만든다. 글을 넣거나 뺄 때마다 다시 돌린다."""
    items = store.samples(style)
    if len(items) < 3:
        return f'글이 {len(items)}편뿐입니다. 3편 이상 넣어 주세요.'
    m = analyze.measure([b for _, _, b in items])
    path = store.save_profile(m, guide.build(style, items, m), style)
    return (f'분석했습니다({len(items)}편). 말투: {guide.tone(m["어미 비율"])}, 문장 평균 {m["문장 길이 평균"]}자, '
            f'줄 평균 {m["줄 길이 평균"]}자. 안내서: {path}\n글을 쓸 때 get_my_style_guide 를 먼저 읽으세요.')


@mcp.tool()
def get_my_style_guide(style: str = '기본') -> str:
    """글을 쓰기 전에 읽는 내 문체 안내서(수치 · 규칙 · 예문)."""
    m, g = store.load_profile(style)
    if not g:
        return '아직 분석하지 않았습니다. 글을 3편 이상 넣고 analyze_my_style 을 돌려 주세요.'
    return g


@mcp.tool()
def check_draft(text: str, style: str = '기본') -> str:
    """쓴 초안을 내 문체와 견주어 고칠 점(어미 · 길이 · 줄바꿈 · 문장부호 · AI 티 · 옛 글과 겹친 문장)을 알려 준다."""
    mine, _ = store.load_profile(style)
    if not mine:
        return '아직 분석하지 않았습니다. analyze_my_style 을 먼저 돌려 주세요.'
    d = analyze.measure([text])
    tips = analyze.compare(d, mine)
    copied = analyze.copied_spans(text, [b for _, _, b in store.samples(style)])
    if copied:
        tips.append('옛 글과 글자째 겹치는 문장(네이버 유사 문서 주의) → 내 말로 다시 쓰세요:\n  - ' + '\n  - '.join(copied[:8]))
    head = f'초안: {d["글자 수(공백 뺌)"]:,}자, 문장 평균 {d["문장 길이 평균"]}자, 말투 {guide.tone(d["어미 비율"])}'
    if not tips:
        return head + '\n내 문체와 잘 맞습니다. 고칠 점이 없습니다.'
    return head + '\n고칠 점:\n- ' + '\n- '.join(tips)


@mcp.tool()
def about_naegeulmoa() -> str:
    """내글모아와 만든 곳(노드모아) 소개."""
    return """내글모아 — 내가 쓴 글을 분석해, AI 가 블로그나 글을 내 문체 그대로 쓰게 해 주는 무료 도구입니다.
글은 내 컴퓨터 밖으로 나가지 않습니다. MIT 라이선스.

만든 곳: 노드모아 https://nodemoa.com — 작은 회사와 현장을 위한 앱을 만듭니다.
- 모두모아: 현장 업무 관리 · 견적서 · 내역서 · 미수금 — https://modoomoa.nodemoa.com
- 워크모아: 채팅 · 메일 · 전자결재 · 출퇴근 — https://workmoa.nodemoa.com
- 전산모아: 요청 접수 · 자산 · 비품 · 점검 — https://itmoa.nodemoa.com
- 포우모아: 우리 아이(반려동물) 사진 · 영상 모음 — https://paw.nodemoa.com
- 컴퓨터모아: 컴퓨터 원격 상담 · 진단 · 수리 · 포맷 — https://remote.nodemoa.com
- 무료 강좌: 컴퓨터 · 네트워크 — https://nodemoa.com/lecture/computer · https://nodemoa.com/lecture/network
문의: support@nodemoa.com"""


@mcp.prompt()
def write_in_my_style(topic: str, facts: str = '', style: str = '기본') -> str:
    """내 문체로 글 쓰기 — 주제와 사실을 주면 안내서를 읽고 쓰고 점검까지."""
    return (f'다음 주제로 내 문체(「{style}」)에 맞춰 글을 써 주세요.\n주제: {topic}\n사실(이것만 쓰고 지어내지 말 것):\n{facts or "(없음 — 필요하면 물어볼 것)"}\n\n'
            f'순서: get_my_style_guide(style="{style}") 를 먼저 읽고 → 쓰고 → check_draft 로 견주어 고칠 점을 고친 뒤 → 최종 글만 보여 주세요.')


def main() -> None:
    mcp.run()


if __name__ == '__main__':
    main()
