"""네이버 블로그에서 내 글 가져오기 — 공개 글만, 최근 글 위주(네이버 RSS 가 주는 범위).

내 블로그 글만 가져오세요. 남의 글로 문체를 배우면 사칭 · 표절이 될 수 있습니다(내글모아는 본인 여부를 알 수 없습니다).
"""
from __future__ import annotations

import html
import re
import time
import urllib.parse
import urllib.request

from . import __version__

UA = f'naegeulmoa/{__version__} (+https://nodemoa.com)'
MAX_BYTES = 3_000_000   # 한 번 받는 응답 상한
TIMEOUT = 15            # 요청 하나의 제한 시간(초)
TOTAL_SECONDS = 120     # 가져오기 전체 제한 시간(초)
_HOSTS = {'blog.naver.com', 'm.blog.naver.com', 'rss.blog.naver.com'}
_ID = re.compile(r'[A-Za-z0-9_\-]{3,40}')
_NOT_ID = {'postview', 'postlist', 'prologue', 'blogid', 'naver', 'postview.naver', 'postlist.naver', 'prologue.naver'}


def _get(url: str) -> str:
    host = urllib.parse.urlsplit(url).hostname or ''
    if host not in _HOSTS:
        raise ValueError('네이버 블로그 주소만 가져올 수 있습니다.')
    req = urllib.request.Request(url, headers={'User-Agent': UA})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
        if (urllib.parse.urlsplit(r.geturl() or url).hostname or '') not in _HOSTS:
            raise ValueError('네이버 밖 주소로 넘어가서 멈췄습니다.')
        data = r.read(MAX_BYTES + 1)
    if len(data) > MAX_BYTES:
        raise ValueError('응답이 너무 커서 멈췄습니다.')
    return data.decode('utf-8', errors='replace')


def blog_id_of(url_or_id: str) -> str:
    """「blog.naver.com/아이디」 · 「…/PostView.naver?blogId=아이디&logNo=…」 · 「m.blog.naver.com/아이디/…」 · 아이디만."""
    s = (url_or_id or '').strip()
    if _ID.fullmatch(s) and s.lower() not in _NOT_ID:
        return s
    u = urllib.parse.urlsplit(s if '://' in s else 'https://' + s)
    if (u.hostname or '') not in _HOSTS:
        raise ValueError('네이버 블로그 주소(blog.naver.com/아이디)나 아이디를 넣어 주세요.')
    q = urllib.parse.parse_qs(u.query)
    for key in ('blogId', 'blogid'):
        if q.get(key) and _ID.fullmatch(q[key][0]):
            return q[key][0]
    first = next((p for p in u.path.split('/') if p), '')
    if u.hostname == 'rss.blog.naver.com':
        first = first.removesuffix('.xml')
    if _ID.fullmatch(first) and first.lower() not in _NOT_ID:
        return first
    raise ValueError('주소에서 블로그 아이디를 찾지 못했습니다. blog.naver.com/아이디 꼴로 넣어 주세요.')


def _between(x: str, start: str, end: str) -> list[str]:
    """start … end 사이 조각들(정규식 없이 — 닫는 표시가 없는 큰 문서에서도 느려지지 않게)."""
    out, i = [], 0
    while True:
        a = x.find(start, i)
        if a < 0:
            return out
        a += len(start)
        b = x.find(end, a)
        if b < 0:
            return out
        out.append(x[a:b])
        i = b + len(end)


def _tag(item: str, name: str) -> str:
    got = _between(item, f'<{name}>', f'</{name}>')
    if not got:
        return ''
    v = got[0].replace('<![CDATA[', '').replace(']]>', '')
    return re.sub(r'\s+', ' ', html.unescape(v)).strip()


def recent_posts(blog: str, limit: int = 10) -> list[dict]:
    bid = blog_id_of(blog)
    x = _get(f'https://rss.blog.naver.com/{bid}.xml')
    out = []
    for item in _between(x, '<item>', '</item>')[:limit]:
        link = _tag(item, 'link')
        m = re.search(r'/(\d{9,})', link) or re.search(r'logNo=(\d+)', link)
        if m:
            out.append({'blog': bid, 'no': m.group(1), 'title': _tag(item, 'title')[:200]})
    return out


def post_text(blog: str, no: str) -> str:
    bid = blog_id_of(blog)
    if not re.fullmatch(r'\d{1,20}', str(no)):
        raise ValueError('글 번호가 이상합니다.')
    q = urllib.parse.urlencode({'blogId': bid, 'logNo': no, 'redirect': 'Dlog', 'widgetTypeCall': 'true', 'directAccess': 'false'})
    x = _get(f'https://blog.naver.com/PostView.naver?{q}')
    lines = []
    for chunk in _between(x, '<p class="se-text-paragraph', '</p>'):
        body = chunk.split('>', 1)[1] if '>' in chunk else ''
        lines.append(html.unescape(re.sub(r'<[^<>]{0,2000}>', '', body)).replace(chr(0x200B), '').strip())
    text = '\n'.join(lines).strip()
    return re.sub(r'\n{3,}', '\n\n', text)


def deadline() -> float:
    return time.monotonic() + TOTAL_SECONDS
