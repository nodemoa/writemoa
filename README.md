# 내글모아 (writemoa)

**내가 쓴 글을 분석해, AI가 블로그나 글을 _내 문체로_ 쓰게 돕는 무료 MCP 서버**

> 만든 곳: **[노드모아 (nodemoa.com)](https://nodemoa.com)** — 작은 회사와 현장을 위한 앱을 만듭니다.
> 무료 · MIT 라이선스 · 넣은 글은 내 컴퓨터에 저장

AI에게 블로그 글을 맡기면 맞는 말인데 「내 글 같지」가 않습니다. 말끝도, 문장 길이도, 줄 바꾸는 버릇도 다르기 때문입니다.
내글모아는 내가 이미 쓴 글에서 그 버릇을 숫자와 예문으로 정리한 **문체 안내서**를 만들고, AI가 쓴 초안을 **내 글과 견주어 무엇이 다른지** 짚어 줍니다.

> **MCP가 뭔가요?** AI 프로그램(Claude 등)에 도구를 붙이는 표준 방식입니다. 내글모아를 붙이면 AI가 대화 중에 「내 글 넣기 · 문체 안내서 읽기 · 초안 점검」을 스스로 부릅니다.
> 내 컴퓨터에서 도는 도구라 **Claude 데스크톱 앱 · Claude Code** 처럼 컴퓨터에 설치하는 프로그램에서 씁니다. claude.ai 웹 · 휴대폰 앱에서는 쓸 수 없습니다.

## 그냥 AI에게 내 글 몇 편 보여 주면 되지 않나요?

그것도 됩니다. 다만 그렇게 하면 이런 일이 자주 생깁니다.

| 그냥 보여 줄 때 | 내글모아를 쓸 때 |
|---|---|
| 말투가 한두 문단 지나면 「~합니다」 같은 AI 말투로 돌아감 | 다 쓴 뒤 `check_draft` 가 **말투 · 줄바꿈 · 버릇이 내 글과 얼마나 다른지** 숫자로 짚음(문장 하나하나를 짚지는 않음) |
| 「다양한 · 효과적으로 · 알아보겠습니다」 같은 AI 티 나는 말이 섞임 | 내 글에 없는 **AI 투 말 · 과장된 홍보 말**을 찾아 줌 |
| 보여 준 글의 문장을 그대로 가져다 씀 | **옛 글과 똑같은 문장**을 찾아 줌(같은 문장이 많으면 검색에서 중복 글로 보일 수 있음) |
| Claude 프로젝트 · 스타일에 넣어 두면 그 안에서는 되지만, 쓰는 AI 프로그램마다 따로 넣어야 함 | 한 번 넣어 두면 연결한 프로그램 어디서나 씀 · 네이버 블로그에서 바로 가져옴 |
| 블로그 · 공지 · 업무 메일을 한데 섞어 배움 | **글 종류별로** 따로 배우고, 종류마다 지켜야 할 기본(공지의 문의처 등)도 점검 |

## 무엇을 재나요

내 글 3편 이상(많을수록 정확)에서:

- **말투** — 해요체 · 합니다체 · ~다 · 반말 · 음슴체(~했음) · 개조식(~함 · ~됨) 비율, 그리고 ~잖아요 · ~더라고요 · ~거든요 같은 끝말
- **글 모양** — 문장 길이 · 줄 길이 · 한 문장을 여러 줄로 나눠 쓰는지 · 문단 수 · 글 길이
- **버릇** — 느낌표 · 물음표 · 말줄임 · 물결 · ㅋㅋ · ㅎㅎ · 이모지 · 해시태그 · 쉼표를 1,000자에 몇 번 쓰는지(가격의 쉼표, 「10시~6시」의 물결은 빼고 셈)
- **낱말** — 자주 쓰는 부사 · 이음말(막상 · 사실 · 그래서 …), 의성어 · 의태어(쏙 · 톡톡 · 보송보송), 독자를 부르는 말(여러분 · 이웃님), 「저 · 제가」, 돈 표기(3만 원 / 30,000원)
- **처음과 끝** — 제목 · 첫 줄 · 끝 줄. 여러 글에 되풀이되는 인사는 「늘 쓰는 첫 줄」로 따로 알려 줍니다

한국 블로그는 한 문장을 여러 줄로 나눠 쓰는 경우가 많아, 내글모아는 줄을 이어 문장을 다시 만든 뒤에 말끝을 봅니다.

## 글 종류

같은 사람도 블로그와 공지, 업무 메일의 문체가 다릅니다. 그래서 글마다 종류를 두고, **같은 종류 글이 2편 이상이면 그 종류만의 안내서**를 따로 만듭니다.

| 아이디 | 종류 | 안내서에 붙는 기본 | 점검: 꼭 있어야 하는 것 |
|---|---|---|---|
| `blog-info` | 블로그(정보형) | 검색 낱말을 넣은 제목, 공감 → 소제목 → 정리, 네이버에서는 마크다운을 쓰지 않음 | — |
| `blog-review` | 블로그(후기 · 리뷰형) | 사실 먼저, 불편 → 써 보니 → 장단점 → 누구에게, 대가를 받았으면 「광고 · 협찬」을 제목이나 첫 부분에(공정위 추천 · 보증 심사지침) | 가격(또는 무료) |
| `essay` | 에세이 · 칼럼 | 경험 → 생각 → 여운, 소제목보다 문단 흐름 | — (해시태그는 짚음) |
| `paper` | 논문 · 연구 보고서 | 학술 평서체, 주장마다 출처, 용어 정의, 감정 표현 · 구어 금지 | 근거 · 출처(저자, 연도) |
| `work-doc` | 업무 문서(기획서 · 업무 보고 · 회의록) | 개조식, 결론 먼저, 날짜 · 담당 · 기한 · 수치 | 날짜 · 기한 |
| `notice` | 공지 · 안내문 | 합니다체, 일시 · 장소 · 대상 · 내용 · 문의처 | 날짜 · 시간, 문의처 |
| `email` | 업무 이메일 · 메시지 | 인사 → 용건 → 내용 → 요청 · 기한 → 맺음 | 받는 사람 · 인사, 맺음말 |
| `sns` | SNS 짧은 글 | 짧게, 첫 줄에서 눈길, 광고 표시 | — (15줄 넘으면 짚음) |
| `lecture` | 강의 · 설명글 | 질문으로 열고 단계별로, 예시 · 비유, 끝에 정리 · 퀴즈 | 예시 · 비유 |
| `press` | 보도자료 · 홍보문 | 배포 날짜, 역피라미드, 3인칭과 관계자 인용, 회사 소개 · 문의처 | 문의처 |

**종류는 이렇게 정합니다.**

1. 사용자가 알려 주면(「이건 공지야」) 그대로 씁니다. 가장 정확합니다.
2. 알려 주지 않으면 말투 비율 · 개조식과 목록 줄 · 출처 표시 · 해시태그와 이모지 · 받는 사람과 맺음말 · 종류별 낱말(1,000자당)로 짐작합니다.
   **1등이 2등보다 확실히 높을 때만** 종류를 정하고, 아니면 「종류 미정」으로 둡니다(미정인 글도 전체 문체에는 들어갑니다).
   종류를 잘못 정하면 엉뚱한 글과 견주게 되므로, 틀린 종류보다 미정을 택하도록 맞췄습니다.
   새로 지은 시험 글 98편(두 묶음)에서 확실하다고 정한 45편 가운데 42편(93%)이 맞았고, 나머지 53편은 미정으로 남았습니다.

**점검은 이렇게 견줍니다.**

- 종류를 안 주면 → 내 글 전체와 견줍니다.
- 그 종류 내 글이 2편 이상 → 그 종류 글과 견줍니다(전부 봄).
- 블로그 · 후기 · SNS인데 그 종류 글이 모자라면 → 내 블로그 같은 글과 말투 · 줄바꿈 · 낱말 · 문장부호를 견줍니다(글 길이 · 문장 길이는 종류마다 달라서 뺌).
- 그 밖의 종류(에세이 · 강의 · 공지 · 이메일 · 논문 · 업무 문서 · 보도자료)인데 그 종류 글이 모자라면 → 그 종류의 기본을 먼저 따르고, 내가 안 쓰는 버릇(웃음 · 이모지 · AI 투 말 …)만 짚습니다.
- 공지 · 이메일 · 논문 · 업무 문서 · 보도자료는 **정해진 말투**도 점검합니다(해요체로 쓴 공지 → 「합니다체로 씁니다」).

## 설치

### 1. uv 설치(한 번만)

[uv](https://docs.astral.sh/uv/)는 파이썬 프로그램을 따로 설치하지 않고 바로 실행해 주는 도구입니다.

- **맥:** 「터미널」 앱을 열고 붙여 넣은 뒤 Enter
  ```bash
  curl -LsSf https://astral.sh/uv/install.sh | sh
  ```
- **윈도우:** 시작 메뉴에서 「PowerShell」을 열고 붙여 넣은 뒤 Enter
  ```powershell
  powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
  ```

설치가 끝나면 uv가 어디에 있는지 확인해 둡니다(다음 단계에서 씁니다).

- 맥: 터미널에서 `which uvx` → 예: `/Users/내이름/.local/bin/uvx`
- 윈도우: PowerShell에서 `where.exe uvx` → 예: `C:\Users\내이름\.local\bin\uvx.exe`

> 새 판이 나오면 주소의 `0.3.0` 두 곳을 새 판 번호로 바꿉니다. [Releases](https://github.com/nodemoa/writemoa/releases) 에서 판 번호를 볼 수 있습니다.

### 2. Claude Desktop에 연결

1. Claude Desktop → **설정 → 개발자 → 설정 편집**을 누르면 `claude_desktop_config.json` 파일이 열립니다.
2. 파일이 비어 있으면 아래를 통째로 붙여 넣습니다. `"command"` 에는 1단계에서 확인한 uvx 경로를 넣습니다(윈도우는 `\` 를 `\\` 로 두 번).
   ```json
   {
     "mcpServers": {
       "writemoa": {
         "command": "/Users/내이름/.local/bin/uvx",
         "args": ["--from", "https://github.com/nodemoa/writemoa/releases/download/v0.3.0/writemoa-0.3.0-py3-none-any.whl", "writemoa"]
       }
     }
   }
   ```
   이미 다른 서버가 있으면 `"mcpServers": { … }` 안에 `"writemoa": { … }` 한 덩어리만 쉼표로 이어 넣습니다.
3. Claude를 **완전히 종료**했다가 다시 켭니다(맥: 메뉴 막대의 Claude → 종료, 윈도우: 작업 표시줄 오른쪽 아이콘 → 종료). 창만 닫으면 바뀐 설정이 적용되지 않습니다.
4. 대화창 아래 도구 단추에 「writemoa」가 보이면 연결된 것입니다.

### Claude Code

```bash
claude mcp add writemoa -- uvx --from https://github.com/nodemoa/writemoa/releases/download/v0.3.0/writemoa-0.3.0-py3-none-any.whl writemoa
```

### 그 밖의 MCP 프로그램(Cursor 등)

명령 `uvx`, 인자 `--from https://github.com/nodemoa/writemoa/releases/download/v0.3.0/writemoa-0.3.0-py3-none-any.whl writemoa` 로 등록합니다.

> ChatGPT는 지금 인터넷 주소가 있는 서버형 MCP만 연결할 수 있어, 내 컴퓨터에서 도는 내글모아는 아직 쓸 수 없습니다.

## 쓰는 법

AI에게 평소 말로 부탁하면 됩니다.

1. **내 글 모으기**
   - 「내 네이버 블로그 blog.naver.com/내아이디 에서 글 10편 가져와 줘」
   - 또는 글을 붙여 넣고 「이 글 내 글모음에 넣어 줘(종류는 공지)」
   - 넣을 때마다 분석은 저절로 됩니다.
2. **쓰기** — 「아래 내용으로 내 문체로 블로그 글 써 줘: (사실 · 숫자 · 제품 정보)」
   AI가 안내서를 읽고 → 쓰고 → 점검하고 → 고친 글을 보여 줍니다. 공지 · 이메일처럼 종류가 정해진 글이면 「공지로」 라고 덧붙여 주세요.
3. **확인** — 「내 문체 요약 보여 줘」, 「내가 넣은 글 목록 보여 줘」

### 도구

| 도구 | 하는 일 |
|---|---|
| `add_my_writing` | 내가 쓴 글 한 편 넣기(100자 이상, 종류는 선택) |
| `import_my_naver_blog` | 내 네이버 블로그 최근 공개 글 가져오기(최대 30편, 이미 있는 글은 건너뜀) |
| `list_my_writings` | 넣은 글 목록(번호 · 종류 · 제목 · 글자 수) |
| `read_my_writing` | 넣은 글 한 편 보기 |
| `remove_my_writing` | 넣은 글 지우기 |
| `set_writing_kind` | 글 종류 바꾸기 |
| `list_writing_kinds` | 글 종류 열 가지 |
| `analyze_my_style` | 내 문체 요약 보기 |
| `get_my_style_guide` | 글 쓰기 전에 읽는 문체 안내서(종류별) |
| `check_draft` | 초안을 내 글과 견주어 고칠 점 알려 주기(제목은 따로 받아 본문 수치에서 뺌) |
| `list_styles` | 문체 묶음 목록(회사용 · 개인용처럼 나눈 경우) |
| `about_writemoa` | 내글모아 · 노드모아 소개 |

프롬프트 `write_in_my_style`(주제 · 종류 · 사실 · 문체 묶음)도 들어 있습니다.

## 내 글은 어디로 가나요

- 넣은 글과 분석 결과는 **내 컴퓨터**의 `~/.writemoa/` 폴더에 저장합니다(`WRITEMOA_HOME` 으로 바꿀 수 있음). 내글모아가 따로 어딘가로 보내지는 않습니다.
- 다만 글을 넣고, 안내서를 읽고, 초안을 점검하는 동안 그 내용(넣은 글 · 안내서의 예문 · 초안)은 **지금 쓰는 AI 서비스(Claude 등)로 전달됩니다.** AI가 읽어야 쓸 수 있기 때문이고, 그 서비스의 개인정보 정책이 함께 적용됩니다.
- 네이버 블로그 가져오기는 공개 글을 읽기만 합니다.
- 글을 지우면 분석도 그 글을 빼고 다시 합니다. 글이 3편 아래로 줄면 옛 안내서도 지웁니다.

## 지켜 주세요

- **본인 글만 넣어 주세요.** 남의 블로그나 작가 문체를 흉내 내는 데 쓰면 사칭 · 표절이 될 수 있습니다. 내글모아는 블로그 주인이 본인인지 알 수 없습니다.
- **사실은 내가 줍니다.** 내글모아는 문체를 맞출 뿐, 숫자 · 가격 · 날짜 · 제품 정보는 내가 준 것만 쓰도록 AI에게 안내합니다.

## 한계

- 형태소 분석기 없이 규칙으로 읽습니다. 그래서 명사로 끝나는 말을 반말로 보기도 합니다(「오늘 저녁은 연어.」). 수치는 「대략 이런 버릇」으로 보면 됩니다.
- 종류 짐작은 틀릴 수 있습니다. 확실하지 않으면 미정으로 두니, 중요한 글은 종류를 알려 주세요.
- 점검은 말투 · 길이 · 문장부호 · 낱말 같은 겉모습을 봅니다. 내용이 맞는지, 흐름이 자연스러운지는 직접 읽어 보고 판단해 주세요.

## 만든 곳 — 노드모아

**[노드모아 (nodemoa.com)](https://nodemoa.com)** 는 작은 회사와 현장을 위한 앱을 만듭니다.

| | 하는 일 |
|---|---|
| [무료 강좌](https://nodemoa.com/lecture/computer) | 컴퓨터 · [네트워크](https://nodemoa.com/lecture/network) 기초 강좌 |
| [컴퓨터모아](https://remote.nodemoa.com) | 컴퓨터 원격 상담 · 진단 · 수리 · 포맷 |
| [포우모아](https://paw.nodemoa.com) | 우리 아이(반려동물) 사진 · 영상 모음 |
| [모두모아](https://modoomoa.nodemoa.com) | 현장 업무 관리 · 견적서 · 내역서 · 미수금 |
| [워크모아](https://workmoa.nodemoa.com) | 채팅 · 메일 · 전자결재 · 출퇴근 |
| [전산모아](https://itmoa.nodemoa.com) | 요청 접수 · 자산 · 비품 · 점검 |

문의: support@nodemoa.com

내글모아가 도움이 되셨다면 GitHub 별(★)로 알려 주세요. 다른 분들이 찾는 데 큰 도움이 됩니다.

## 라이선스

MIT — 상업용을 포함해 자유롭게 쓰고 고치고 나눠도 됩니다. 다시 나눌 때는 저작권 표시(© 노드모아)와 MIT 허락 문구(LICENSE 파일)를 함께 남겨 주세요.

---

### English

**writemoa** is a free MCP server that learns *your* Korean writing style from your own posts and helps AI write in your voice. It measures Korean sentence endings and speech levels, sentence/line length, line-break habits, punctuation, onomatopoeia and favorite words, builds a style guide for the AI, and checks drafts against your writing — flagging tone drift, AI-sounding or hype phrases, and sentences copied from your old posts. It keeps separate styles for ten kinds of writing (blog, review, essay, paper, work document, notice, email, SNS, lecture, press release) with the basic conventions of each.
Your writing is stored on your computer (`~/.writemoa`); while you write, the texts are passed to the AI service you use. Made by [Nodemoa](https://nodemoa.com). MIT licensed.
