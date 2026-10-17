import asyncio
import os
import sys

import pytest
from mcp.server.mcpserver.exceptions import ToolError

from naegeulmoa import server as S
from samples import AI_DRAFT, NOTICE


def add3(examples):
    for title, body in examples:
        S.add_my_writing(body, title)


def test_errors_are_korean_tool_errors():
    with pytest.raises(ToolError, match='너무 짧습니다'):
        S.add_my_writing('짧은 글')
    with pytest.raises(ToolError, match='문체 이름'):
        S.list_my_writings(style='a/b')
    with pytest.raises(ToolError, match='3편 이상'):
        S.check_draft(AI_DRAFT)


def test_flow(examples, home):
    add3(examples)
    out = S.add_my_writing(NOTICE, '공지', kind='공지')
    assert '공지 · 안내문' in out and '분석했습니다' in out
    assert '0004' in S.list_my_writings() and '0004' in S.read_my_writing(4)
    g = S.get_my_style_guide()
    assert '내 문체 안내서' in g and 'nodemoa.com' in g
    g2 = S.get_my_style_guide(kind='이메일')
    assert '기본이 먼저' in g2 and '업무 이메일' in g2
    with pytest.raises(ToolError):
        S.check_draft('   ')
    tips = S.check_draft(AI_DRAFT)
    assert 'AI 투 말' in tips and '마크다운' in tips
    same = S.check_draft(examples[0][1])
    assert '똑같은 부분' in same
    assert '안내서 파일:' in S.analyze_my_style()
    from pathlib import Path
    assert S._where(Path.home() / '.naegeulmoa' / '기본' / 'guide.md') == '~/.naegeulmoa/기본/guide.md'


def test_stale_guide_removed(examples, home):
    add3(examples)
    assert (home / '기본' / 'guide.md').exists()
    S.remove_my_writing('1')
    assert not (home / '기본' / 'guide.md').exists()
    with pytest.raises(ToolError):
        S.get_my_style_guide()


def test_set_kind_message(examples):
    add3(examples)
    out = S.set_writing_kind(2, '후기·리뷰')
    assert '「블로그(후기 · 리뷰형)」으로 바꿨습니다' in out


def test_prompt_passes_style():
    p = S.write_in_my_style('프린터', 'blog-info', '', '회사용')
    assert 'check_draft(kind="blog-info", style="회사용")' in p


def test_stdio_round_trip(tmp_path):
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client

    async def run():
        env = dict(os.environ, NAEGEULMOA_HOME=str(tmp_path / 'h'))
        p = StdioServerParameters(command=sys.executable, args=['-m', 'naegeulmoa.server'], env=env)
        async with stdio_client(p) as (r, w):
            async with ClientSession(r, w) as s:
                await s.initialize()
                names = {t.name for t in (await s.list_tools()).tools}
                res = await s.call_tool('add_my_writing', {'text': '짧음'})
                ok = await s.call_tool('list_my_writings', {})
                return names, res, ok
    names, res, ok = asyncio.run(run())
    assert {'add_my_writing', 'check_draft', 'read_my_writing', 'list_writing_kinds'} <= names and len(names) == 12
    assert res.is_error and '너무 짧습니다' in res.content[0].text
    assert '넣은 글이 없습니다' in ok.content[0].text
