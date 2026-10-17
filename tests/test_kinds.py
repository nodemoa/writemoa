import pytest

from naegeulmoa import kinds
from samples import EMAIL, NOTICE, PAPER, REVIEW, SNS


def test_samples():
    for text, want in [(PAPER, 'paper'), (NOTICE, 'notice'), (EMAIL, 'email'), (SNS, 'sns'), (REVIEW, 'blog-review')]:
        assert kinds.detect(text)[0].id == want


def test_examples_are_blog(examples):
    for _, body in examples:
        assert kinds.detect(body)[0].id == 'blog-info'


def test_corpus_accuracy():
    """새로 지어 쓴 64편 — 전체 맞힌 비율, 그리고 「확신」 이라고 한 것의 정확도."""
    from kinds_corpus import C
    res = [(want, *kinds.detect(t)) for want, _, t in C]
    ok = sum(1 for want, k, _, _ in res if k.id == want)
    sure = [(want, k) for want, k, _, s in res if s]
    sure_ok = sum(1 for want, k in sure if k.id == want)
    assert ok / len(res) >= 0.75, ok
    assert sure_ok / max(1, len(sure)) >= 0.9, (sure_ok, len(sure))


def test_find():
    assert kinds.find('후기·리뷰').id == 'blog-review'
    assert kinds.find('블로그(후기 · 리뷰형)').id == 'blog-review'
    assert kinds.find('공지').id == 'notice'
    assert kinds.find('회의록').id == 'work-doc'
    assert kinds.find('논문').id == 'paper'
    assert kinds.find('없는종류') is None
    with pytest.raises(ValueError):
        kinds.find('보고')


def test_norm_issues():
    paper = kinds.BY_ID['paper']
    assert any('느낌표' in m for m in kinds.norm_issues(paper, PAPER + ' 정말 좋다!'))
    assert not any('구어' in m for m in kinds.norm_issues(paper, PAPER + ' 이 방법은 불완전하다. 완전히 다르다.'))
    assert any('문의처' in m for m in kinds.norm_issues(kinds.BY_ID['notice'], '10월 28일 이전합니다. 협조 바랍니다.'))
    assert not kinds.norm_issues(kinds.BY_ID['notice'], NOTICE)
    assert not any('날짜' in m for m in kinds.norm_issues(kinds.BY_ID['notice'], '다음 주 월요일 휴무입니다. 문의는 전화로 주세요.'))


def test_phone_is_not_citation():
    assert kinds.signals('문의 (02-333-4567) 또는 (2024년 기준) 자료')['인용'] == 0
    assert kinds.signals('선행 연구(Kim, 2020)와 [3] 참고')['인용'] == 2
