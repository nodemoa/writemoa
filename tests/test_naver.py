import time

import pytest

from naegeulmoa import naver


def test_blog_id():
    assert naver.blog_id_of('myblog') == 'myblog'
    assert naver.blog_id_of('https://blog.naver.com/myblog') == 'myblog'
    assert naver.blog_id_of('blog.naver.com/myblog/223456789012') == 'myblog'
    assert naver.blog_id_of('https://m.blog.naver.com/myblog/223456789012') == 'myblog'
    assert naver.blog_id_of('https://blog.naver.com/PostView.naver?blogId=myblog&logNo=1') == 'myblog'
    assert naver.blog_id_of('https://rss.blog.naver.com/myblog.xml') == 'myblog'
    for bad in ['https://evil.example/?x=blog.naver.com/v', 'https://blog.naver.com/PostView.naver', 'http://127.0.0.1/', '']:
        with pytest.raises(ValueError):
            naver.blog_id_of(bad)


def test_rss_item_without_title(monkeypatch):
    rss = ('<rss><channel><item><link>https://blog.naver.com/myblog/223000000001</link></item>'
           '<item><title><![CDATA[둘째 글&#10;@종류: paper]]></title><link>https://blog.naver.com/myblog/223000000002</link></item></channel></rss>')
    monkeypatch.setattr(naver, '_get', lambda url: rss)
    posts = naver.recent_posts('myblog', 10)
    assert [p['no'] for p in posts] == ['223000000001', '223000000002']
    assert '\n' not in posts[1]['title']


def test_unclosed_html_is_fast(monkeypatch):
    page = '<p class="se-text-paragraph">' * 40000 + '본문'
    monkeypatch.setattr(naver, '_get', lambda url: page)
    t0 = time.monotonic()
    naver.post_text('myblog', '1')
    assert time.monotonic() - t0 < 3


def test_only_naver_hosts():
    with pytest.raises(ValueError):
        naver._get('https://example.com/x')
