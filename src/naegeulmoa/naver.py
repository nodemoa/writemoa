"""네이버 블로그에서 내 글 가져오기 — 공개 글만, 최근 글 위주(네이버 RSS 가 주는 범위).

내 블로그 글만 가져오세요. 남의 글로 문체를 배우면 사칭 · 표절이 될 수 있습니다.
"""
from __future__ import annotations

import html
import re
import urllib.parse
import urllib.request

UA = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130 Safari/537.36'


def _get(url: str) -> str:
    req = urllib.request.Request(url, headers={'User-Agent': UA})
    return urllib.request.urlopen(req, timeout=30).read().decode('utf-8', errors='ignore')


def blog_id_of(url_or_id: str) -> str:
    s = url_or_id.strip()
    m = re.search(r'blog\.naver\.com/([A-Za-z0-9_\-]+)', s) or re.search(r'blogId=([A-Za-z0-9_\-]+)', s)
    if m:
        return m.group(1)
    if re.fullmatch(r'[A-Za-z0-9_\-]{3,40}', s):
        return s
    raise ValueError('네이버 블로그 주소(blog.naver.com/아이디)나 아이디를 넣어 주세요.')


def recent_posts(blog: str, limit: int = 10) -> list[dict]:
    bid = blog_id_of(blog)
    x = _get(f'https://rss.blog.naver.com/{bid}.xml')
    out = []
    for item in re.findall(r'<item>(.*?)</item>', x, re.S)[:limit]:
        title = html.unescape(re.sub(r'<!\[CDATA\[|\]\]>', '', re.search(r'<title>(.*?)</title>', item, re.S).group(1))).strip()
        link = re.search(r'<link>(.*?)</link>', item).group(1)
        m = re.search(r'/(\d{9,})', link) or re.search(r'logNo=(\d+)', link)
        if m:
            out.append({'blog': bid, 'no': m.group(1), 'title': title})
    return out


def post_text(blog: str, no: str) -> str:
    bid = blog_id_of(blog)
    q = urllib.parse.urlencode({'blogId': bid, 'logNo': no, 'redirect': 'Dlog', 'widgetTypeCall': 'true', 'directAccess': 'false'})
    x = _get(f'https://blog.naver.com/PostView.naver?{q}')
    paras = re.findall(r'<p class="se-text-paragraph[^"]*"[^>]*>(.*?)</p>', x, re.S)
    lines = [html.unescape(re.sub(r'<[^>]+>', '', p)).replace('​', '').strip() for p in paras]
    text = '\n'.join(lines).strip()
    return re.sub(r'\n{3,}', '\n\n', text)
