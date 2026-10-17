"""글 종류 — 같은 사람도 블로그 · 논문 · 공지 · 업무 메일의 문체가 다르다.

종류마다 (1) 그 종류의 일반 규범(안내서에 붙임), (2) 점검 규칙, (3) 알아보는 신호를 둔다.
사람의 버릇은 종류마다 따로 재고, 그 종류 글이 없으면 「내 공통 버릇 + 그 종류 규범」 으로 쓴다.
종류 짐작은 낱말 · 말투 규칙이라 틀릴 수 있다. 확신이 없으면 「종류 미정」 으로 두고, 사람이 정한 종류를 늘 먼저 쓴다.
"""
from __future__ import annotations

import collections
import re
from dataclasses import dataclass, field

from . import analyze


@dataclass
class Kind:
    id: str
    name: str
    about: str
    norms: list[str]
    must: list[tuple[str, str]] = field(default_factory=list)   # (정규식, 무엇) — 꼭 있어야 하는 것
    avoid: list[tuple[str, str]] = field(default_factory=list)  # (정규식, 있으면 할 말) — 있으면 안 되는 것
    aliases: tuple[str, ...] = ()                                # 찾을 때 받아 주는 다른 이름
    free: tuple[str, ...] = ()                                   # 이 종류에서 원래 쓰는 것(문장부호 · 낱말) — 내 버릇과 달라도 짚지 않음
    tones: tuple[str, ...] = ()                                  # 이 종류의 말투(비어 있으면 사람 따라)


_AD_RULE = ('대가(돈 · 무료 제공 · 할인 포함)를 받은 글이면 「광고」 · 「협찬」 같은 말을 제목이나 글 첫 부분에 밝힌다'
            '(공정거래위원회 「추천 · 보증 등에 관한 표시 · 광고 심사지침」).')
_CASUAL = r'(?<![가-힣])(?:진짜|엄청|대박|되게)(?=\s|로|[.!?,]|$)'  # 「완전」 은 「완전 경쟁 시장」 처럼 학술 용어에도 쓰여 뺌
_FORMAL_OK = ('또한', '이를 통해', '다양한', '효과적', '체계적', '중요합니다', '뿐만 아니라', '원활한', '최적화', '필수적', '아래와 같이', '~하는 것이 좋습니다', '이처럼', '핵심은', '극대화')  # 격식 글에서는 흔한 말 — AI 투 말로 짚지 않음

KINDS: list[Kind] = [
    Kind('blog-info', '블로그(정보형)', '정보 · 방법을 알려 주는 블로그 글',
         ['제목에 찾는 사람이 검색할 낱말을 넣는다.', '도입에서 독자의 상황에 공감한 뒤, 소제목별로 정보를 풀고, 끝에 정리한다.',
          '문단은 짧게, 사진 자리를 둔다. 해시태그는 내 버릇만큼.', '네이버 블로그는 마크다운(**굵게** · ## 제목)이 글자 그대로 보이니 쓰지 않는다.'],
         avoid=[(r'\[\d{1,3}\]|et al\.|참고문헌', '논문식 인용 표시는 블로그에 어울리지 않습니다.')],
         aliases=('블로그', '정보', '정보 글', '블로그 글', '포스팅')),
    Kind('blog-review', '블로그(후기 · 리뷰형)', '제품 · 장소 · 서비스를 써 보고 쓴 후기',
         ['제품 이름 · 가격 같은 사실을 먼저 정확히.', '쓰기 전 불편 → 써 보니 → 좋은 점 · 아쉬운 점 → 누구에게 맞는지.',
          '느낌을 살리는 말(의성어 · 의태어 · 감각어)을 쓰되 과장하지 않는다.', _AD_RULE],
         must=[(r'(?<![\d,])\d[\d,]*\s*[만천]?\s*원|가격|무료|공짜', '가격(또는 무료) 정보')],
         aliases=('후기', '리뷰', '사용기', '맛집', '체험')),
    Kind('essay', '에세이 · 칼럼', '생각 · 경험을 풀어내는 글',
         ['「~다」 평서체가 기본(해요체 에세이도 있으니 내 글을 따른다).', '한 가지 생각을 끝까지 밀고 간다 — 경험 → 생각 → 여운.',
          '소제목보다 문단의 흐름으로.'],
         avoid=[(r'(?<![#\w])#[^\s#]+', '에세이에 해시태그는 어울리지 않습니다.')],
         aliases=('에세이', '칼럼', '수필', '일기', '단상'), free=('따옴표', '해시태그 #')),
    Kind('paper', '논문 · 연구 보고서', '연구 · 분석 · 조사 결과를 쓰는 글',
         ['「~이다 · ~한다 · ~하였다」 학술 평서체.', '주장마다 근거와 출처(저자, 연도)를 붙인다.', '용어는 처음 나올 때 정의한다.',
          '서론 → 본론 → 결론, 1인칭 대신 「본 연구는」.', '감정 표현 · 구어 · 이모지 · 느낌표를 쓰지 않는다.'],
         avoid=[(r'!|ㅋ|ㅎㅎ|ㅜ|ㅠ', '논문 · 보고서에 느낌표 · 웃음이 있습니다.'),
                (_CASUAL, '논문 · 보고서에 구어 강조어(진짜 · 엄청 · 대박 …)가 있습니다.'),
                (r'(해요|예요|에요|잖아요|거든요)[.!?]?\s*$', '논문 · 보고서에 「~요」 말투가 섞여 있습니다.')],
         must=[(r'\([가-힣A-Za-z][^()\n]{0,40}?(?:19|20)\d{2}[a-z]?\)|\[\d{1,3}\]|에 따르면|에 의하면', '근거 · 출처 표시(저자, 연도)')],
         aliases=('논문', '연구', '학술', '연구 보고서', '학위 논문', '리포트'), free=('따옴표', '쉼표 ,', *_FORMAL_OK), tones=('~다 평서체',)),
    Kind('work-doc', '업무 문서(기획서 · 업무 보고 · 회의록)', '회사 안에서 쓰는 문서',
         ['개조식(~함 · ~임 · ~예정)과 번호 목록.', '결론 · 요청을 맨 앞에.', '날짜 · 담당 · 기한 · 수치(단위 포함)를 분명히.'],
         avoid=[(r'ㅋ|ㅎㅎ|ㅜ|ㅠ', '업무 문서에 웃음이 있습니다.')], tones=('개조식', '~다 평서체', '합니다체', '명사로 끝'),
         must=[(r'\d{1,2}\s*[월/.]\s*\d{1,2}|\d{4}[-.]\d{1,2}|기한|까지|[월화수목금]요일|다음 ?주|이번 ?주', '날짜 · 기한')],
         aliases=('업무', '업무 문서', '업무 보고', '업무 보고서', '보고서', '기획서', '회의록', '품의서'), free=('쉼표 ,', '마크다운(**굵게** · ## 제목)', *_FORMAL_OK)),
    Kind('notice', '공지 · 안내문', '여러 사람에게 알리는 글',
         ['합니다체. 제목에 무엇을 알리는지 쓴다.', '필요한 항목(일시 · 장소 · 대상 · 내용 · 문의처)을 빠짐없이.', '바뀐 점은 눈에 띄게, 맺음은 「바랍니다 · 감사합니다」.'],
         must=[(r'\d{1,2}\s*[월/.]\s*\d{1,2}|\d{1,2}\s*시|일시|기간|[월화수목금토일]요일|오늘|내일|모레|다음 ?주|이번 ?주|부터|까지', '날짜 · 시간'),
               (r'문의|연락|전화|☎|@|\d{2,4}-\d{3,4}-\d{4}|담당', '문의처')],
         avoid=[(r'ㅋ|ㅎㅎ|ㅜ|ㅠ', '공지에 웃음 표시가 있습니다.')], tones=('합니다체', '명사로 끝', '개조식'),
         aliases=('공지', '안내', '안내문', '공지사항', '알림'), free=('쉼표 ,', *_FORMAL_OK)),
    Kind('email', '업무 이메일 · 메시지', '사람에게 보내는 업무 연락',
         ['인사(○○님, 안녕하세요. ~입니다) → 용건 한 줄 → 자세한 내용 → 요청 · 기한 → 맺음(감사합니다. ~ 드림).', '존댓말, 첨부가 있으면 언급.'],
         must=[(r'안녕하|님\s*[,，]', '받는 사람 · 인사'), (r'감사|드림|올림|부탁드립니다|고맙습니다', '맺음말')],
         avoid=[(r'ㅋ|ㅎㅎ|ㅜ|ㅠ', '업무 메일에 웃음 표시가 있습니다.')], tones=('합니다체', '해요체', '명사로 끝'),
         aliases=('이메일', '메일', '메시지', '업무 메일', '편지'), free=_FORMAL_OK),
    Kind('sns', 'SNS 짧은 글', '인스타 · 스레드 · 페이스북 같은 짧은 글',
         ['한두 줄에서 다섯 줄 안팎.', '첫 줄에서 눈길을 끈다.', '해시태그 · 이모지는 내 버릇만큼.', _AD_RULE],
         avoid=[(r'^(?:[^\n]*\n){15,}', 'SNS 글로는 너무 깁니다(15줄 넘음).')],
         aliases=('sns', '인스타', '인스타그램', '스레드', '페이스북', 'x', '트위터')),
    Kind('lecture', '강의 · 설명글', '차근차근 가르치는 글',
         ['질문으로 열고 단계별로 설명한다.', '예시 · 비유로 쉽게, 어려운 용어는 풀어 쓴다.', '끝에 정리 · 퀴즈.'],
         must=[(r'예를 들|예시|처럼|비유|가령', '예시 · 비유')],
         aliases=('강의', '설명', '설명글', '강좌', '교재', '튜토리얼'), free=('물음표 ?', '따옴표')),
    Kind('press', '보도자료 · 홍보문', '언론 · 대외에 알리는 글',
         ['맨 위에 배포 날짜(또는 「즉시 보도」)와 제목 · 부제.', '역피라미드: 누가 · 무엇을 · 언제를 첫 문단에.',
          '3인칭(「○○는 ~했다고 밝혔다」), 관계자 인용문.', '끝에 회사 소개와 문의처(담당 · 연락처). 과장 표현은 빼고 사실만.'],
         avoid=[(r'ㅋ|ㅎㅎ|ㅜ|ㅠ|!!', '보도자료에 웃음 · 겹느낌표가 있습니다.')],
         must=[(r'문의|연락처|담당|홈페이지|@|\d{2,4}-\d{3,4}-\d{4}', '문의처(담당 · 연락처)')],
         aliases=('보도자료', '보도', '홍보', '홍보문', '기사'), free=('따옴표', '쉼표 ,', *_FORMAL_OK), tones=('~다 평서체', '합니다체', '명사로 끝')),
]
BY_ID = {k.id: k for k in KINDS}
# 블로그 같은 글 — 말투(해요체 · 합니다체 …)가 종류보다 사람을 따르는 글. 이것끼리는 말투 · 낱말 · 줄바꿈을 견줘도 된다.
# (에세이 · 강의는 「~다」 · 합니다체가 흔해 블로그 말투와 견주지 않는다)
CASUAL = {'blog-info', 'blog-review', 'sns'}


def _flat(s: str) -> str:
    return re.sub(r'[\s·・ㆍ,_\-()]', '', s).lower()


def find(kind: str) -> Kind | None:
    """아이디 · 이름 · 다른 이름으로 종류 찾기. 띄어쓰기 · 가운뎃점은 따지지 않는다(「후기·리뷰」 = 「후기 · 리뷰」).

    없으면 None, 여러 종류에 걸치면(예: 「보고」) ValueError — 후보를 알려 준다.
    """
    k = _flat(kind or '')
    if not k:
        return None
    for x in KINDS:
        if k in (_flat(x.id), _flat(x.name)) or k in (_flat(a) for a in x.aliases):
            return x
    hits = [x for x in KINDS if k in _flat(x.name) or any(k in _flat(a) for a in x.aliases)]
    if len(hits) == 1:
        return hits[0]
    if len(hits) > 1:
        raise ValueError(f'「{kind}」 는 여러 종류에 걸칩니다: ' + ', '.join(f'{x.id}({x.name})' for x in hits) + '. 아이디로 골라 주세요.')
    return None


_LISTLINE = re.compile(r'^\s*(?:[-•·*▶▷✔✓☞]|\d{1,2}[.)]\s|[①-⑳]|[가나다라마바사아자차카타파하][.)]\s)')
_CITE = re.compile(r'\([가-힣A-Za-z][^()\n]{0,40}?(?:19|20)\d{2}[a-z]?\)|\[\d{1,3}\]|et al\.|참고문헌')
_TITLE_RECIPIENT = re.compile(r'(?:과장|부장|팀장|대리|차장|실장|대표|이사|사원|주임|선생|교수|담당자|원장|소장|매니저)\s?님')
_NOT_RECIPIENT = ('여러분', '이웃', '구독자', '독자', '회원', '고객', '시청자', '방문자', '친구')


def _recipient(first: str) -> bool:
    m = re.match(r'^\s*([^\n,，.!]{1,15})님\s*[,，]', first)
    if m and not any(w in m.group(1) for w in _NOT_RECIPIENT):
        return True
    return bool(_TITLE_RECIPIENT.search(first)) and len(first) <= 60


def _words(*ws: str) -> re.Pattern:
    """낱말 목록 → 정규식. 낱말 앞이 한글이면 세지 않는다(「인공지능」 속 「공지」 를 공지로 세지 않게)."""
    return re.compile(r'(?<![가-힣])(?:' + '|'.join(ws) + ')')


def _phrases(*ps: str) -> re.Pattern:
    return re.compile('|'.join(ps))


_W = {
    '연구': (_words('본 연구', '선행 ?연구', '연구 결과', '분석 결과', '조사 결과', '연구 대상', '연구 방법', '가설', '표본', '유의미', '통계적',
                  '시사점', '한계점', '참고문헌', '응답자', '설문', '조사 개요', '원인 분석', '집계', '변인', '실험군', '대조군'),
             _phrases('분석하였다', '조사하였다', '나타났다', '확인되었다', '검토하였다', '살펴보았다', '판단된다', '것으로 보인다', '분석된다', '로 나타났')),
    '메일': (_words('첨부', '회신', '송부', '말씀드린', '말씀하신', '검토 부탁', '확인 부탁', '연락 ?주시면', '전달드립니다', '보내 ?드립니다'),
             _phrases(r'드립니다\.?\s*$')),
    '공지': (_words('일시', '장소', '대상', '기간', '신청', '접수', '문의', '공지', '변경', '유의', '협조', '참석', '운영 ?시간', '휴무', '안내드립니다',
                  '알려드립니다', '이용', '주민', '입주민', '회원'),
             _phrases('바랍니다', '주시기 바랍니다', '하시기 바랍니다', '예정입니다')),
    '후기': (_words('후기', '리뷰', '가성비', '장점', '단점', '내돈내산', '별점', '재구매', '만족', '아쉬운', '아쉬웠', '맛집', '배송', '맛있',
                  '웨이팅', '메뉴', '친절', '관람', '직접 써', '한 달 써', '구매', '추천'),
             _phrases('써 ?보니', '사용해 ?보니', '먹어 ?보', '다녀왔', '다녀온', '가 ?봤', '봤는데', '읽었다', '읽고 나서', '★')),
    '강의': (_words('예를 들', '정리하면', '퀴즈', '연습 ?문제', '강좌', '강의', '수업', '개념', '원리', '쉽게 말해', '다시 말해', '지난 ?시간',
                  '지난번', '다음 ?시간', '오늘 배운', '복습', '숙제', '공식', '정의', '예제', '문제를 풀'),
             _phrases('볼까요', '봅시다', '알아봅시다', '기억해 ?두', '뜻합니다', '뜻한다', '라고 합니다', '이라고 합니다', '라고 부릅', '이라고 부릅',
                      '이해하', '배워', '배운', '배울', '살펴봅', '번째 ?시간', '연습해', '해 봅시다', '구해 보')),
    '보도': (_words('관계자', '보도자료', '대표이사', '즉시 보도', '배포일', '밝혔다', '전했다', '말했다', '강조했다', '덧붙였다', '설명했다'),
             _phrases('출시했다', '발표했다', '예정이다', '선보인다', '선보였다', '체결했다', '개최한다', '개최했다', '제공한다', '밝혔습니다', '전했습니다',
                      '말했습니다', '개최합니다', '에 따르면', '대표는', '시장은', '청장은', '구청장', '시청은', '구청은')),
    '업무': (_words('담당', '기한', '일정', '안건', '결정 ?사항', '회의', '검토', '진행 ?상황', '요청 ?사항', '참석자', '예산', '마감', '협의', '결재',
                  '품의', '향후 계획', '조치', '보고'),
             _phrases(r'(?<!\d)\d+월 ?\d+일까지')),
    '정보': (_words('방법', '정리', '소개', '팁', '설정', '순서', '주의', '차이', '비교', '이유', '꿀팁', '하는 ?법'),
             _phrases('알려 ?드릴', '확인하', '해 ?보세요', '하시면', '하면 됩니다', '좋아요', '좋습니다')),
    '생각': (_words('생각', '마음', '기억', '문득', '돌아보면', '삶', '어쩌면', '아마도', '그때', '그날', '우리는', '인생', '세월', '나이'),
             _phrases('느꼈다', '싶다', '것이다', '않을까', '던 ?날', '았다', '었다', '였다')),
}


def _count(name: str, t: str) -> int:
    a, b = _W[name]
    return len(a.findall(t)) + len(b.findall(t))


def signals(text: str) -> dict:
    t = analyze.clean(text)
    sents = analyze.sentences(t)
    n = max(1, len(sents))
    lines = [ln.strip() for ln in t.split('\n') if ln.strip()]
    lv = collections.Counter(analyze.level_of(s) for s in sents)
    chars = len(re.sub(r'\s', '', t))
    per = 1000 / max(chars, 600)  # 낱말 수는 1,000자당. 짧은 글이 낱말 하나로 부풀지 않게 600자 아래는 600자로 봄
    first = lines[0] if lines else ''
    tail = '\n'.join(lines[-2:])

    def c(p: str, flags: int = 0) -> int:
        return len(re.findall(p, t, flags))

    out = {
        '길이': chars, '줄 수': len(lines), '문장 수': len(sents),
        '해요': lv['해요체'] / n, '합니다': lv['합니다체'] / n, '다': lv['~다 평서체'] / n,
        '반말': (lv['반말'] + lv['음슴체']) / n, '개조식': lv['개조식'] / n, '명사': lv['명사로 끝'] / n,
        '목록 줄': sum(1 for ln in lines if _LISTLINE.match(ln)) / max(1, len(lines)),
        '소제목': c(r'^\s*(?:#{1,4}\s|■|【|\[[^\]\n]{2,30}\]\s*$|\*\*[^*\n]{1,60}\*\*\s*$)', re.M),
        '인용': len(_CITE.findall(t)),
        '해시태그': c(r'(?<![#\w])#[^\s#]+'), '이모지': analyze.count_emoji(t), '느낌표': t.count('!'),
        '웃음': c(r'ㅋ+|ㅎ{2,}|[ㅜㅠ]+'),
        '인사': bool(re.search(r'안녕하(?:세요|십니까)', '\n'.join(lines[:3]))),
        '받는 사람': _recipient(first),
        '맺음': bool(re.search(r'(?:드림|올림)\s*$', tail)),
        '맺음 약': bool(re.search(r'(?:감사합니다|부탁드립니다|고맙습니다)[.!]?\s*$', tail)),
        '1인칭 저': c(r'(?<![가-힣])(?:저는|제가|저도|저희)'), '1인칭 나': c(r'(?<![가-힣])(?:나는|내가|나도|나의)'),
        '독자 부르기': c(r'여러분|이웃님|구독자님|독자님'),
        '인용 말': c(r'["“][^"”\n]{5,120}["”]\s*(?:고|라고|이라고)\s*(?:말했|밝혔|전했|설명했|강조했)'),
        '머리 칸': c(r'^\s*(?:수신|발신|작성자?|제목|참조|문서 ?번호|보고자|결재|보고 ?일자|작성일)\s*[:：]', re.M),
        '메일 낱말': _count('메일', t),
    }
    for name, key in (('연구', '연구 낱말'), ('공지', '공지 낱말'), ('후기', '후기 낱말'), ('강의', '강의 낱말'), ('보도', '보도 낱말'),
                      ('업무', '업무 낱말'), ('정보', '정보 낱말'), ('생각', '생각 낱말')):
        out[key] = per * _count(name, t)
    return out


def scores(text: str) -> dict[str, tuple[float, list[str]]]:
    s = signals(text)
    sc: dict[str, float] = {k.id: 0.0 for k in KINDS}
    why: dict[str, list[str]] = {k.id: [] for k in KINDS}

    def add(kid: str, v: float, reason: str) -> None:
        if v:
            sc[kid] += v
            if v > 0 and reason:
                why[kid].append(reason)

    yo = s['해요'] + s['합니다']
    add('paper', 3 * min(s['인용'], 3), f'출처 표시 {s["인용"]}곳')
    add('paper', 0.6 * min(s['연구 낱말'], 10), '연구 · 분석 낱말')
    add('paper', 1.5 if s['다'] > 0.6 and s['느낌표'] == 0 and s['웃음'] == 0 and s['1인칭 나'] == 0 and s['연구 낱말'] >= 2 else 0, '「~다」 학술체')

    add('essay', 1 if s['다'] > 0.5 and s['인용'] == 0 else 0, '「~다」 평서')
    add('essay', 0.3 * min(s['생각 낱말'], 14), '생각 · 경험 낱말')
    add('essay', 1 if s['1인칭 나'] >= 2 else 0, '「나는 · 내가」')
    add('essay', -2 if s['소제목'] >= 2 or s['해시태그'] >= 2 or s['목록 줄'] > 0.2 else 0, '')
    add('essay', -1 if s['후기 낱말'] >= 4 or s['강의 낱말'] >= 4 or s['보도 낱말'] >= 3 else 0, '')

    worky = s['목록 줄'] > 0.2 or s['업무 낱말'] >= 8 or s['머리 칸'] >= 1
    add('work-doc', (4 * s['개조식']) * (1 if worky else 0.3) + 2.5 * s['목록 줄'], f'개조식 {int(s["개조식"]*100)}% · 목록 줄 {int(s["목록 줄"]*100)}%')
    add('work-doc', 0.35 * min(s['업무 낱말'], 12), '업무 낱말(담당 · 기한 · 회의 …)')
    add('work-doc', 1.5 * min(s['머리 칸'], 3), '수신 · 제목 같은 머리 칸')

    add('notice', 0.45 * min(s['공지 낱말'], 14), '공지 낱말(일시 · 장소 · 문의 …)')
    add('notice', 1 if s['합니다'] > 0.5 and s['공지 낱말'] >= 6 else 0, '합니다체로 알림')
    add('notice', -1.5 if s['받는 사람'] else 0, '')
    add('notice', -1.5 if s['보도 낱말'] >= 4 or s['인용 말'] else 0, '')

    add('email', 3 if s['받는 사람'] else 0, '받는 사람(○○님,)')
    add('email', (2 if s['맺음'] else 0) + (0.8 if s['맺음 약'] else 0), '맺음말')
    add('email', 0.5 if s['인사'] and s['받는 사람'] else 0, '인사')
    add('email', 0.7 * min(s['메일 낱말'], 4), '첨부 · 회신 같은 말')

    add('sns', 0.5 * min(s['해시태그'], 8) + 0.3 * min(s['이모지'], 6), f'해시태그 {s["해시태그"]} · 이모지 {s["이모지"]}')
    add('sns', 1.5 if s['길이'] < 200 and s['줄 수'] <= 8 and s['합니다'] < 0.5 and not (s['인사'] or s['받는 사람'] or s['맺음']) else 0, '아주 짧은 글')
    add('sns', 1.5 if s['반말'] + s['명사'] + s['개조식'] > 0.5 and s['길이'] < 450 and s['목록 줄'] < 0.2 and s['머리 칸'] == 0 else 0, '반말 · 음슴체로 짧게')
    add('sns', -1.5 if s['소제목'] >= 2 or s['길이'] > 900 else 0, '')

    add('blog-review', 0.45 * min(s['후기 낱말'], 14), '후기 낱말(써 보니 · 장단점 · 맛있 …)')
    add('blog-review', 0.15 * min(s['느낌표'], 10), '')

    add('lecture', 0.45 * min(s['강의 낱말'], 14), '설명 낱말(예를 들어 · 개념 · 볼까요 …)')
    add('lecture', 0.8 if s['독자 부르기'] >= 2 and s['강의 낱말'] >= 3 else 0, '독자를 부르며 설명')

    add('press', 0.6 * min(s['보도 낱말'], 14), '보도 낱말(밝혔다 · 관계자 …)')
    add('press', 2 * min(s['인용 말'], 2), '따옴표 인용 뒤 「~고 말했다」')
    add('press', 1 if s['다'] > 0.5 and s['1인칭 나'] + s['1인칭 저'] == 0 and s['보도 낱말'] >= 3 else 0, '3인칭 「~다」')

    add('blog-info', 1.5 if s['인사'] and not s['받는 사람'] else 0, '인사로 엶')
    add('blog-info', 1 if yo > 0.6 and s['길이'] > 200 and not s['받는 사람'] else 0, '존댓말로 풂')
    add('blog-info', 0.25 * min(s['정보 낱말'], 14), '방법 · 정리 낱말')
    add('blog-info', 0.8 if s['소제목'] >= 2 else 0, '소제목')
    add('blog-info', 0.3 * min(s['해시태그'], 5) if s['길이'] > 400 else 0, '끝 해시태그')
    return {k: (round(sc[k], 2), why[k]) for k in sc}


SURE_SCORE, SURE_GAP = 2.5, 1.5  # 1등 점수가 이 이상이고 2등보다 이만큼 높을 때만 「확실」


def detect(text: str) -> tuple[Kind, list[str], bool]:
    """글 종류 짐작 — (종류, 그렇게 본 까닭, 확신 여부). 1등과 2등 점수가 가까우면 확신 없음."""
    sc = scores(text)
    rank = sorted(sc.items(), key=lambda kv: -kv[1][0])
    (best, (b, why)), (second, (s2, _)) = rank[0], rank[1]
    if b < 1:
        return BY_ID['blog-info'], ['뚜렷한 신호가 없음'], False
    sure = b >= SURE_SCORE and b - s2 >= SURE_GAP
    reasons = why[:3] + ([] if sure else [f'{BY_ID[second].name}와 비슷함'])
    return BY_ID[best], reasons, sure


def norm_issues(kind: Kind, text: str) -> list[str]:
    """그 종류에 꼭 있어야 하는 것 · 없어야 하는 것 · 정해진 말투."""
    out = []
    if kind.tones:
        sents = analyze.sentences(text)
        if len(sents) >= 3:
            lv = collections.Counter(analyze.level_of(s) for s in sents)
            off = {k: v for k, v in lv.items() if k not in kind.tones}
            if sum(off.values()) / len(sents) > 0.3:
                main = ' · '.join(k for k in kind.tones if k != '명사로 끝')
                got = ', '.join(f'{k} {v * 100 // len(sents)}%' for k, v in sorted(off.items(), key=lambda kv: -kv[1]))
                out.append(f'말투: {analyze.josa("「" + kind.name + "」", "은/는")} {analyze.josa(main, "으로/로")} 씁니다 — 초안에 {got}.')
    for pat, what in kind.must:
        if not re.search(pat, text, re.M):
            out.append(f'빠진 것: {what} — 「{kind.name}」 에 꼭 있어야 합니다.')
    for pat, msg in kind.avoid:
        if re.search(pat, text, re.M):
            out.append(msg)
    return out


def table() -> str:
    return '\n'.join(f'- {k.id} · {k.name}: {k.about}' for k in KINDS)
