"""네이버 블로그에서 내 글 가져오기 — 공개 글만, 최근 글 위주(네이버 RSS 가 주는 범위).

내 블로그 글만 가져오세요. 남의 글로 문체를 배우면 사칭 · 표절이 될 수 있습니다(내글모아는 본인 여부를 알 수 없습니다).
"""
from __future__ import annotations

import html
import re
import socket
import time
import urllib.error
import urllib.parse
import urllib.request

from . import __version__

UA = f'writemoa/{__version__} (+https://nodemoa.com)'
MAX_BYTES = 3_000_000   # 한 번 받는 응답 상한
TIMEOUT = 15            # 요청 하나의 제한 시간(초)
TOTAL_SECONDS = 120     # 가져오기 전체 제한 시간(초)
_HOSTS = {'blog.naver.com', 'm.blog.naver.com', 'rss.blog.naver.com'}  # naver.me 는 짧은 주소 풀 때만
_ID = re.compile(r'[A-Za-z0-9_\-]{3,40}')
_NOT_ID = {'postview', 'postlist', 'prologue', 'blogid', 'naver', 'postview.naver', 'postlist.naver', 'prologue.naver'}


class _OnlyNaver(urllib.request.HTTPRedirectHandler):
    """넘겨 주는 주소를 따라가기 전에 본다 — 네이버 밖으로는 요청 자체를 보내지 않는다."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        if (urllib.parse.urlsplit(newurl).hostname or '') not in _HOSTS:
            raise ValueError('네이버 밖 주소로 넘어가려 해서 멈췄습니다.')
        return super().redirect_request(req, fp, code, msg, headers, newurl)


_OPENER = urllib.request.build_opener(_OnlyNaver)
_END: list[float] = [0.0]  # 가져오기 전체 마감(time.monotonic). 0 이면 없음


def _get(url: str, hosts: set[str] = _HOSTS) -> str:
    host = urllib.parse.urlsplit(url).hostname or ''
    if host not in hosts:
        raise ValueError('네이버 블로그 주소만 가져올 수 있습니다.')
    timeout = TIMEOUT
    if _END[0]:
        left = _END[0] - time.monotonic()
        if left <= 1:
            raise ValueError('가져오는 시간이 너무 길어져 멈췄습니다. 글 수를 줄여 다시 해 주세요.')
        timeout = min(TIMEOUT, left)
    req = urllib.request.Request(url, headers={'User-Agent': UA})
    try:
        with _OPENER.open(req, timeout=timeout) as r:
            data = r.read(MAX_BYTES + 1)
    except urllib.error.HTTPError as e:
        if e.code == 404:
            raise ValueError('그 블로그(또는 글)를 찾지 못했습니다. 주소 · 아이디가 맞는지, 글이 전체 공개인지 확인해 주세요.') from None
        raise ValueError(f'네이버가 요청을 받지 않았습니다(HTTP {e.code}). 잠시 뒤 다시 해 주세요.') from None
    except (urllib.error.URLError, socket.timeout, TimeoutError, ConnectionError, OSError):
        raise ValueError('네이버에 연결하지 못했습니다. 인터넷 연결을 확인하고 잠시 뒤 다시 해 주세요.') from None
    if len(data) > MAX_BYTES:
        raise ValueError('응답이 너무 커서 멈췄습니다.')
    return data.decode('utf-8', errors='replace')


def _short_link(s: str) -> str:
    """naver.me 짧은 주소 → 실제 블로그 주소(네이버 안에서 넘겨 주는 곳만 따라감)."""
    u = urllib.parse.urlsplit(s if '://' in s else 'https://' + s)
    if u.hostname != 'naver.me':
        return s
    req = urllib.request.Request(urllib.parse.urlunsplit(('https', 'naver.me', u.path, '', '')), headers={'User-Agent': UA}, method='HEAD')
    try:
        with _OPENER.open(req, timeout=TIMEOUT) as r:
            return r.geturl()
    except ValueError:
        raise
    except Exception:
        raise ValueError('짧은 주소(naver.me)를 열지 못했습니다. blog.naver.com/아이디 꼴로 넣어 주세요.') from None


def blog_id_of(url_or_id: str) -> str:
    """「blog.naver.com/아이디」 · 「…/PostView.naver?blogId=아이디&logNo=…」 · 「m.blog.naver.com/아이디/…」 · 아이디만."""
    s = (url_or_id or '').strip()
    if _ID.fullmatch(s) and s.lower() not in _NOT_ID:
        return s
    if 'naver.me' in s:
        s = _short_link(s)
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


def start_deadline() -> None:
    _END[0] = time.monotonic() + TOTAL_SECONDS


def end_deadline() -> None:
    _END[0] = 0.0
