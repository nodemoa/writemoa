import pytest

from naegeulmoa import kinds
from samples import EMAIL, NOTICE, PAPER, REVIEW, SNS


def test_samples():
    for text, want in [(PAPER, 'paper'), (NOTICE, 'notice'), (EMAIL, 'email'), (SNS, 'sns'), (REVIEW, 'blog-review')]:
        assert kinds.detect(text)[0].id == want


def test_examples_are_blog(examples):
    for _, body in examples:
        assert kinds.detect(body)[0].id == 'blog-info'


def _rate(data):
    res = [(want, *kinds.detect(t)) for want, _, t in data]
    ok = sum(1 for want, k, _, _ in res if k.id == want)
    sure = [(want, k) for want, k, _, s in res if s]
    return ok / len(res), sum(1 for want, k in sure if k.id == want) / max(1, len(sure)), len(sure) / len(res)


def test_corpus_accuracy():
    """새로 지어 쓴 두 묶음(64편 · 34편). 짐작은 틀릴 수 있으니 「확실」 이라고 정한 것의 정확도를 높게 지킨다(틀린 종류로 넣는 것보다 미정이 낫다)."""
    from kinds_corpus import C
    from kinds_corpus2 import N
    for data in (C, N):
        ok, sure_ok, sure_share = _rate(data)
        assert ok >= 0.6, ok
        assert sure_ok >= 0.85, sure_ok
        assert sure_share >= 0.35, sure_share
    ok, sure_ok, _ = _rate(C + N)
    assert sure_ok >= 0.9, sure_ok


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


def test_fixed_tone():
    issues = kinds.norm_issues(kinds.BY_ID['notice'], '사무실 이전해요ㅎㅎ\n10월 28일부터 새 사무실이에요~\n김대리한테 편하게 물어보세요~\n문의는 02-123-4567')
    assert any('합니다체' in m for m in issues) and any('웃음' in m for m in issues)
    assert not any('말투' in m for m in kinds.norm_issues(kinds.BY_ID['notice'], NOTICE))


def test_word_boundary():
    assert kinds.signals('인공지능 기술을 소개합니다. 인공지능은 빠르게 발전합니다.')['공지 낱말'] == 0
