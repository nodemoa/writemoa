# 내글모아 (naegeulmoa)

**내가 쓴 글을 분석해, AI가 블로그나 글을 _내 문체 그대로_ 쓰게 해 주는 무료 MCP 서버**

> 만든 곳: **[노드모아 (nodemoa.com)](https://nodemoa.com)** — 작은 회사와 현장을 위한 앱을 만듭니다.
> 무료 · MIT 라이선스 · 글은 내 컴퓨터 밖으로 나가지 않습니다.

AI에게 블로그 글을 맡기면 맞는 말인데 「내 글 같지」가 않습니다. 말끝도, 문장 길이도, 줄 바꾸는 버릇도 다르기 때문입니다.
내글모아는 내가 이미 쓴 글을 읽고 그 버릇을 숫자와 예문으로 정리한 **문체 안내서**를 만듭니다. AI는 글을 쓰기 전에 이 안내서를 읽고, 다 쓴 뒤에는 **내 문체와 얼마나 닮았는지 점검**해서 고칩니다.

## 무엇을 해 주나요

- **문체 분석** — 내 글 3편 이상(많을수록 정확)에서
  - 말끝(어미): ~습니다 · ~해요 · ~잖아요 · ~고요 · ~다 … 를 얼마나 쓰는지
  - 문장 길이 · 줄 길이 · 한 문장을 여러 줄로 끊어 쓰는지
  - 문장부호 버릇: 느낌표, 말줄임(..), 물결(~), ㅋㅋ · ㅎㅎ · ㅜㅜ, 이모지
  - 흉내말(보송보송 · 쏙 · 톡), 자주 쓰는 부사 · 이음말(막상 · 사실 · 그래서 …), 문장을 여는 말
  - 제목 · 첫 줄 · 끝 줄을 쓰는 방식
- **문체 안내서** — 위 수치 + 지킬 것 + 예문을 AI가 읽기 좋은 한 장으로
- **초안 점검** — AI가 쓴 글을 내 문체와 견주어
  - 어긋난 곳(말투 · 길이 · 줄바꿈 · 문장부호)
  - 내가 거의 안 쓰는 「AI 티 나는 말」(다양한 · 효과적으로 · 알아보겠습니다 …)
  - **옛 글과 글자째 겹치는 문장** — 그대로 베끼면 네이버 「유사 문서」로 검색에서 밀릴 수 있어 미리 짚습니다
- **네이버 블로그에서 내 글 가져오기** — 주소만 넣으면 최근 공개 글을 가져옵니다
- **문체 여러 개** — 「블로그용」 · 「공지용」처럼 나눠 둘 수 있습니다

## 왜 한국어 전용인가요

영어용 문체 도구는 여럿 있지만 한국어 글은 제대로 읽지 못합니다. 한국 블로그는 한 문장을 여러 줄로 끊어 쓰는 경우가 많아, 줄을 이어 문장을 다시 만든 뒤에야 말끝이 제대로 보입니다(줄 단위로 읽으면 말끝의 70% 넘게를 놓칩니다). 내글모아는 처음부터 한국어 말끝 · 띄어쓰기 · 블로그 줄바꿈에 맞춰 만들었습니다.

## 설치

[uv](https://docs.astral.sh/uv/)가 필요합니다(파이썬 프로그램을 설치 없이 바로 실행해 주는 도구).

```bash
# macOS · Linux
curl -LsSf https://astral.sh/uv/install.sh | sh
# Windows (PowerShell)
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### Claude Desktop

설정 → 개발자 → 설정 편집(`claude_desktop_config.json`)에 넣고 Claude를 다시 켭니다.

```json
{
  "mcpServers": {
    "naegeulmoa": {
      "command": "uvx",
      "args": ["--from", "git+https://github.com/nodemoa/naegeulmoa", "naegeulmoa"]
    }
  }
}
```

### Claude Code

```bash
claude mcp add naegeulmoa -- uvx --from git+https://github.com/nodemoa/naegeulmoa naegeulmoa
```

### 그 밖의 MCP 프로그램(Cursor 등)

명령 `uvx`, 인자 `--from git+https://github.com/nodemoa/naegeulmoa naegeulmoa` 로 등록합니다.

> ChatGPT는 지금 인터넷 주소가 있는 서버형 MCP만 연결할 수 있어, 내 컴퓨터에서 도는 내글모아는 아직 쓸 수 없습니다.

## 쓰는 법

AI에게 평소 말로 부탁하면 됩니다.

1. **내 글 모으기**
   - 「내 네이버 블로그 blog.naver.com/내아이디 에서 글 10편 가져와 줘」
   - 또는 글을 붙여 넣고 「이 글 내 글모음에 넣어 줘」
2. **분석** — 「내 문체 분석해 줘」
3. **쓰기** — 「아래 내용으로 내 문체로 블로그 글 써 줘: (사실 · 숫자 · 제품 정보)」
   AI가 안내서를 읽고 → 쓰고 → 점검하고 → 고친 글을 보여 줍니다.

### 도구

| 도구 | 하는 일 |
|---|---|
| `add_my_writing` | 내가 쓴 글 한 편 넣기(100자 이상) |
| `import_my_naver_blog` | 내 네이버 블로그 최근 공개 글 가져오기(최대 30편) |
| `list_my_writings` / `remove_my_writing` | 넣은 글 보기 · 빼기 |
| `analyze_my_style` | 문체 분석 → 안내서 만들기 |
| `get_my_style_guide` | 글 쓰기 전에 읽는 내 문체 안내서 |
| `check_draft` | 초안을 내 문체와 견주어 고칠 점 알려 주기 |
| `list_styles` | 만들어 둔 문체 목록 |
| `about_naegeulmoa` | 내글모아 · 노드모아 소개 |

프롬프트 `write_in_my_style`(주제 · 사실 · 문체 이름)도 들어 있습니다.

## 내 글은 어디에 저장되나요

모두 내 컴퓨터의 `~/.naegeulmoa/<문체 이름>/` 에만 둡니다(`NAEGEULMOA_HOME` 으로 바꿀 수 있음). 내글모아는 어디로도 글을 보내지 않습니다.
네이버 블로그 가져오기는 공개 글을 읽기만 합니다. 실제 글쓰기는 내가 쓰는 AI(Claude 등)가 하므로, 그 AI 서비스의 개인정보 정책이 함께 적용됩니다.

## 지켜 주세요

- **본인 글만 넣어 주세요.** 남의 블로그나 작가 문체를 흉내 내는 데 쓰면 사칭 · 표절이 될 수 있습니다.
- **사실은 내가 줍니다.** 내글모아는 문체를 맞출 뿐, 숫자 · 가격 · 날짜 · 제품 정보는 내가 준 것만 쓰도록 AI에게 안내합니다.

## 만든 곳 — 노드모아

**[노드모아 (nodemoa.com)](https://nodemoa.com)** 는 작은 회사와 현장을 위한 앱을 만듭니다.

| 앱 | 하는 일 |
|---|---|
| [모두모아](https://modoomoa.nodemoa.com) | 현장 업무 관리 · 견적서 · 내역서 · 미수금 |
| [워크모아](https://workmoa.nodemoa.com) | 채팅 · 메일 · 전자결재 · 출퇴근 |
| [전산모아](https://itmoa.nodemoa.com) | 요청 접수 · 자산 · 비품 · 점검 |
| [포우모아](https://paw.nodemoa.com) | 우리 아이(반려동물) 사진 · 영상 모음 |
| [컴퓨터모아](https://remote.nodemoa.com) | 컴퓨터 원격 상담 · 진단 · 수리 · 포맷 |

무료 강좌: [컴퓨터](https://nodemoa.com/lecture/computer) · [네트워크](https://nodemoa.com/lecture/network)
문의: support@nodemoa.com

내글모아가 도움이 되셨다면 GitHub 별(★)로 알려 주세요. 다른 분들이 찾는 데 큰 도움이 됩니다.

## 라이선스

MIT — 상업용을 포함해 자유롭게 쓰고 고치고 나눠도 됩니다. 저작권 표시(노드모아)만 남겨 주세요.

---

### English

**naegeulmoa** is a free MCP server that learns *your* Korean writing style from your own posts and helps AI write blog posts in your voice. It measures Korean sentence endings, sentence/line length, line-break habits, punctuation, onomatopoeia and favorite words, builds a style guide for the AI, and checks drafts against your style — including AI-sounding phrases and sentences copied from your old posts. Everything stays on your computer. Made by [Nodemoa](https://nodemoa.com). MIT licensed.
