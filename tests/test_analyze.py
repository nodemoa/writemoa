import time

from writemoa import analyze as A

LEVELS = [
    ('같이 가요.', '해요체'), ('정말 맛있어요😊', '해요체'), ('좋았어요(웃음)', '해요체'), ('진짜 좋아요 :)', '해요체'),
    ('진짜 좋아요 👍👍', '해요체'), ('좋아요 🇰🇷', '해요체'), ('좋더라고요.', '해요체'), ('물론이죠.', '해요체'),
    ('그는 “좋습니다”', '합니다체'), ('이게 맞습니까?', '합니다체'), ('다음 장으로 넘어갑시다.', '합니다체'), ('잠시만 기다려 주십시오.', '합니다체'),
    ('그게 진짜 맛있거든.', '반말'), ('생각보다 맛있더라.', '반말'), ('뭐 먹을까?', '반말'), ('비가 온대.', '반말'), ('그렇다니까.', '반말'),
    ('정말 좋네.', '반말'), ('그럴 줄 알았지.', '반말'),
    ('추가 검토 필요.', '개조식'), ('회의 일정 확정함.', '개조식'), ('담당자 지정 예정.', '개조식'),
    ('오늘 점심은 피자.', '명사로 끝'), ('만족도 ★★★★☆', '명사로 끝'), ('결과는 아래와 같다:', '~다 평서체'),
]


def test_levels():
    wrong = [(s, A.level_of(s), want) for s, want in LEVELS if A.level_of(s) != want]
    assert not wrong, wrong


def test_fine_endings():
    assert A.ending_of('정말 편하잖아요ㅋㅋ') == '~잖아요'
    assert A.ending_of('오 분이면 충분합니다.') == '~습니다/ㅂ니다'
    assert A.ending_of('생각보다 좋더라고요') == '~더라고요'


def test_sentences():
    assert A.sentences('머리 감고 나서\n수건으로 말면\n툭 풀리잖아요.\n이건 쏙 끼우면 돼요!') == [
        '머리 감고 나서 수건으로 말면 툭 풀리잖아요.', '이건 쏙 끼우면 돼요!']
    banmal = '오늘 진짜 피곤하네\n아침부터 비 오고\n버스도 놓쳤거든\n그래도 커피는 맛있더라'
    assert len(A.sentences(banmal)) == 3
    listed = A.sentences('## 끄는 법\n1. 전원을 끕니다.\n2. 선을 뽑습니다.\n- 다시 켭니다\n#태그 #둘')
    assert listed == ['전원을 끕니다.', '선을 뽑습니다.', '다시 켭니다']
    assert A.sentences('첫째는 이것입니다. 둘째는 저것입니다.\n셋째는 2026') == ['첫째는 이것입니다.', '둘째는 저것입니다.', '셋째는 2026']


def test_counts_skip_numbers():
    m = A.measure(['가격은 189,000원이고 운영은 10시~6시입니다. 그래서, 좋아요~ 정말 좋아요.'])
    assert m['1000자당']['쉼표 ,'] > 0 and m['1000자당']['물결 ~'] > 0
    only_num = A.measure(['가격은 189,000원이고 운영은 10시~6시입니다. 정말 좋습니다.'])
    assert only_num['1000자당']['쉼표 ,'] == 0 and only_num['1000자당']['물결 ~'] == 0


def test_nfd_same_as_nfc():
    import unicodedata
    s = '오늘은 날씨가 좋네요. 산책을 다녀왔어요.'
    assert A.measure([unicodedata.normalize('NFD', s)])['어미 비율'] == A.measure([s])['어미 비율']


def test_ai_tells_no_false_positive():
    human = '둘째 낳고 첫째가 많이 컸어요. 이에 대해 남편과 이야기했는데, 그렇다면 이사를 가자고 하더라고요.'
    assert not A.measure([human])['AI 티 나는 말']


def test_long_input_fast():
    t0 = time.monotonic()
    A.measure(['ㅋ' * 40000 + '가'])
    A.measure(['(' + '1234 ' * 20000])
    A.measure(['가' * 200000])
    assert time.monotonic() - t0 < 5


def test_compare_needs_more_than_one():
    mine = A.measure(['오늘은 날씨가 좋아요. 산책을 했어요. 바람이 시원했어요? 꽃도 폈어요. 사진도 찍었어요. 집에 왔어요.'] * 3)
    draft = A.measure(['오늘은 날씨가 좋아요. 산책을 했어요. 바람이 시원했어요. 꽃도 폈어요. 사진도 찍었어요. 가 보세요.'])
    tips = A.compare(draft, mine)
    assert not any('세요' in t for t in tips)


def test_copied_spans():
    old = ['노트북 배터리는 80%에서 충전을 멈추게 해 두면 오래 갑니다. 설정에서 한 번만 켜 두면 신경 쓸 일이 없습니다.\n감사합니다.',
           '공유기 비밀번호는 처음 그대로 두면 위험합니다. 관리 화면에 들어가 바로 바꿔 두세요.\n감사합니다.']
    hits, ratio = A.copied_spans(old[0], old)
    assert hits and ratio > 0.8
    hits, ratio = A.copied_spans('새로 쓴 글입니다. 오늘은 마우스 이야기를 합니다.\n감사합니다.', old)
    assert not hits and ratio < 0.15


def test_hype_and_stuffing():
    mine = A.measure(['퇴근하고 쓰는 글이에요. 솔직히 국밥은 다 비슷하다고 생각했어요. 막상 먹어 보니 국물이 맑더라고요. 가격은 9,000원이에요.'] * 3)
    ad = A.measure(['솔직히 만족도가 정말 높은 카페거든요. 솔직히 가성비가 뛰어나요. 솔직히 강력 추천해요. 후회하지 않으실 거예요.'])
    tips = ' '.join(A.compare(ad, mine))
    assert '과장된 홍보 말' in tips and '몰아 넣은' in tips


def test_modes():
    mine = A.measure(['오늘은 날씨가 좋아요. 산책을 했어요. 바람이 시원했어요. 꽃도 폈어요. 사진도 찍었어요.'] * 3)
    formal = A.measure(['오늘은 날씨가 좋습니다. 산책을 했습니다. 바람이 시원했습니다. 꽃도 피었습니다. 사진도 찍었습니다.'])
    assert any('말투' in t for t in A.compare(formal, mine, mode='family'))
    assert not any('말투' in t for t in A.compare(formal, mine, mode='loose'))


def test_round2_endings_and_lines():
    assert A.ending_of('그건 제가 할 수 있지요.') == '~죠'
    assert A.ending_of('같이 갈래요?') == '~어요/아요'
    for s in ['접수는 10월 31일까지', '결과는 아래 이미지', '자세한 건 공지 메시지', '대상: 회원 누구나', '오늘은 동창 모임.', '모든 게 처음.', '벌써 봄.']:
        assert A.level_of(s) == '명사로 끝', s
    assert A.level_of('어제 드디어 그 영화 봤음.') == '음슴체'
    assert A.level_of('말씀은 잘 알겠습니다만') == '합니다체'
    assert len(A.sentences('막상 써 보니,\n생각보다 훨씬 가볍고\n손에 착 감겨서\n하루 종일 들고 다녔어요.')) == 1
    assert len(A.sentences('막상 먹어 보니까\n국물이 맑더라고요.')) == 1
    assert len(A.sentences('어제 그 카페 갔어\n분위기 완전 좋아\n커피도 맛있어\n다음에 같이 가자')) == 4
    assert A.sentences('네. 말씀하신 자료 보내 드립니다.')[0] == '네.'


def test_round2_counts():
    m = A.measure(['쫄깃쫄깃한 떡이 말랑말랑해요. 운영은 오전 10시 ~ 오후 4시, 월~금입니다. 머리가 똑똑해요.'])
    assert '쫄깃쫄깃' in m['흉내말'] and '말랑말랑' in m['흉내말'] and '똑똑' not in m['흉내말']
    assert m['횟수']['물결 ~'] == 0
    human = '확인하는 것이 좋습니다. 무엇보다 한눈에 보기 좋아요. 주말엔 힐링했어요. 꼭 한 번 더 확인해 주세요.'
    tips = A.compare(A.measure([human]), A.measure(['평범한 내 글입니다. 오늘은 날씨가 좋습니다. 산책을 했습니다.'] * 3))
    assert not any('AI 투 말' in t or '과장' in t for t in tips), tips


def test_digits_fast():
    t0 = time.monotonic()
    A.measure(['1' * 20000 + '원', '3' * 20000 + '~5'])
    from writemoa import kinds
    kinds.signals('1' * 20000 + '월 3일까지')
    kinds.norm_issues(kinds.BY_ID['blog-review'], '1' * 20000)
    assert time.monotonic() - t0 < 3


def test_contact_line_not_copied():
    old = ['주차장 공사를 합니다. 지상 주차장을 이용해 주세요.\n문의: 관리사무소 031-777-1212', '정전 점검을 합니다. 엘리베이터가 멈춥니다.']
    hits, _ = A.copied_spans('새 공지입니다. 물탱크를 청소합니다.\n문의: 관리사무소 031-777-1212', old)
    assert not hits
