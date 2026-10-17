"""내 글 보관 — 내 컴퓨터(~/.naegeulmoa 또는 NAEGEULMOA_HOME)에 파일로 저장한다. 내글모아가 어디로 보내지는 않는다.
(다만 글을 쓰고 점검할 때 그 내용은 지금 쓰는 AI 서비스로 전달된다 — AI 가 읽어야 쓸 수 있으므로.)

폴더 모양:
  <집>/<문체 이름>/samples/0001.txt …   내가 쓴 글(한 편 = 파일 하나, 첫 줄 「# 제목」, 둘째 줄 「@종류: blog-info」, 그다음 본문)
  <집>/<문체 이름>/profile.json         분석 수치(전체 · 종류별)
  <집>/<문체 이름>/guide.md             AI 에게 주는 문체 안내서(전체)
  <집>/<문체 이름>/guide-<종류>.md      종류별 안내서(그 종류 글이 2편 이상일 때)
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
import threading
import unicodedata
from pathlib import Path

from . import analyze

DEFAULT = '기본'
LOCK = threading.RLock()  # 같은 프로그램 안에서 글 넣기 · 분석이 겹치지 않게(도구는 여러 줄로 동시에 돌 수 있음)
_SID = re.compile(r'\d{1,6}')
_FILE = re.compile(r'\d{4,6}\.txt')
_RESERVED = {'con', 'prn', 'aux', 'nul', *(f'com{i}' for i in range(1, 10)), *(f'lpt{i}' for i in range(1, 10))}


def home() -> Path:
    return Path(os.environ.get('NAEGEULMOA_HOME', Path.home() / '.naegeulmoa'))


def safe_name(name: str) -> str:
    name = unicodedata.normalize('NFC', name or DEFAULT).strip()
    if not re.fullmatch(r'[0-9A-Za-z가-힣 _\-]{1,40}', name) or name.lower() in _RESERVED:
        raise ValueError('문체 이름은 한글 · 영문 · 숫자 · 띄어쓰기 · _ - 로 40자 안에서 지어 주세요(보통은 비워 두면 「기본」).')
    return name


def safe_sid(sid: str | int) -> str:
    """글 번호 — 숫자만 받는다(「../x」 같은 경로로 다른 파일을 건드리지 못하게)."""
    s = str(sid).strip()
    if not _SID.fullmatch(s):
        raise ValueError(f'글 번호는 숫자입니다(받은 값: {s[:20]}). list_my_writings 로 번호를 확인해 주세요.')
    return s.zfill(4)


def profile_dir(profile: str = DEFAULT, create: bool = True) -> Path:
    d = home() / safe_name(profile)
    if create:
        (d / 'samples').mkdir(parents=True, exist_ok=True)
    return d


def _one_line(s: str) -> str:
    return re.sub(r'\s+', ' ', analyze.clean(s or '')).strip()[:200]


def _write(path: Path, title: str, kind: str, body: str, mode: str = 'w') -> None:
    # 머리 두 줄은 늘 쓴다(제목이 비어도). 본문이 「# 」 이나 「@종류:」 로 시작해도 머리로 읽히지 않게.
    head = f'# {_one_line(title)}\n@종류: {_one_line(kind)}\n'
    with open(path, mode, encoding='utf-8', newline='\n') as f:
        f.write(head + body.strip() + '\n')


def fingerprint(text: str) -> str:
    return hashlib.sha1(re.sub(r'\s+', '', analyze.clean(text)).encode()).hexdigest()[:16]


def add_sample(text: str, title: str = '', profile: str = DEFAULT, kind: str = '') -> str:
    if len(text or '') > analyze.MAX_CHARS:
        raise ValueError(f'글이 너무 깁니다({len(text):,}자). {analyze.MAX_CHARS:,}자까지 받으니 나눠서 넣어 주세요.')
    text = analyze.clean(text).strip()
    if len(re.sub(r'\s', '', text)) < 100:
        raise ValueError('글이 너무 짧습니다. 100자 이상인 글을 넣어 주세요(문체를 읽으려면 문장이 여러 개 있어야 합니다).')
    d = profile_dir(profile) / 'samples'
    fp = fingerprint(text)
    with LOCK:
        for sid, _, _, body in samples(profile):
            if fingerprint(body) == fp:
                raise ValueError(f'같은 글이 이미 있습니다(글 {sid}).')
        nums = [int(p.stem) for p in d.iterdir() if _FILE.fullmatch(p.name)]
        n = (max(nums) + 1) if nums else 1
        for _ in range(1000):  # 다른 프로그램이 같은 번호를 잡아도 덮어쓰지 않게 — 새 파일로만 연다
            sid = f'{n:04d}'
            try:
                _write(d / f'{sid}.txt', title, kind, text, mode='x')
                return sid
            except FileExistsError:
                n += 1
    raise ValueError('글 번호를 잡지 못했습니다. 다시 시도해 주세요.')


def read_sample(path: Path) -> tuple[str, str, str]:
    """(제목, 종류, 본문). 우리 형식이 아닌 글자(cp949 등)가 섞여 있어도 멈추지 않는다."""
    raw = analyze.clean(path.read_text(encoding='utf-8', errors='replace'))
    title = kind = ''
    if raw.startswith('# ') or raw.startswith('#\n'):
        first, _, raw = raw.partition('\n')
        title = first[1:].strip()
    if raw.startswith('@종류:'):
        first, _, raw = raw.partition('\n')
        kind = first.split(':', 1)[1].strip()
    return title, kind, raw.strip()


def samples(profile: str = DEFAULT) -> list[tuple[str, str, str, str]]:
    """(번호, 제목, 종류, 본문) 목록. samples 폴더의 「0001.txt」 꼴 파일만 본다."""
    d = profile_dir(profile, create=False) / 'samples'
    if not d.is_dir():
        return []
    out = []
    for p in sorted(d.iterdir()):
        if _FILE.fullmatch(p.name) and p.is_file():
            title, kind, body = read_sample(p)
            out.append((p.stem, title, kind, body))
    return out


def _sample_path(sid: str | int, profile: str) -> Path:
    return profile_dir(profile, create=False) / 'samples' / f'{safe_sid(sid)}.txt'


def get_sample(sid: str | int, profile: str = DEFAULT) -> tuple[str, str, str] | None:
    p = _sample_path(sid, profile)
    return read_sample(p) if p.is_file() else None


def set_kind(sid: str | int, kind: str, profile: str = DEFAULT) -> bool:
    p = _sample_path(sid, profile)
    if not p.is_file():
        return False
    title, _, body = read_sample(p)
    _write(p, title, kind, body)
    return True


def remove_sample(sid: str | int, profile: str = DEFAULT) -> bool:
    p = _sample_path(sid, profile)
    if p.is_file():
        p.unlink()
        return True
    return False


def profiles() -> list[str]:
    h = home()
    if not h.is_dir():
        return []
    out = []
    for p in h.iterdir():
        try:
            if p.is_dir() and safe_name(p.name) == p.name and (p / 'samples').is_dir():
                out.append(p.name)
        except ValueError:
            continue  # 우리가 만들지 않은 폴더는 건너뜀
    return sorted(out)


def signature(profile: str = DEFAULT, items: list | None = None) -> str:
    """넣은 글이 바뀌었는지 알아보는 값(번호 · 종류 · 본문). items 를 주면 그 목록으로 — 분석에 쓴 글과 서명이 어긋나지 않게."""
    h = hashlib.sha1()
    for sid, _, kind, body in (samples(profile) if items is None else items):
        h.update(f'{sid}|{kind}|{fingerprint(body)}\n'.encode())
    return h.hexdigest()[:16]


def _atomic(path: Path, text: str) -> None:
    """임시 파일에 다 쓴 뒤 바꿔 끼운다 — 쓰다 끊겨도 반쯤 쓴 파일이 남지 않게."""
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix='.tmp-', suffix=path.suffix)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8', newline='\n') as f:
            f.write(text)
        os.replace(tmp, path)
    except BaseException:
        Path(tmp).unlink(missing_ok=True)
        raise


def save_profile(data: dict, guides: dict[str, str], profile: str = DEFAULT) -> Path:
    """guides: {'': 전체 안내서, '<종류>': 종류별 안내서}."""
    d = profile_dir(profile)
    keep = {f'guide-{k}.md' for k in guides if k}
    for old in d.glob('guide-*.md'):
        if old.name not in keep:
            old.unlink(missing_ok=True)
    for kind, text in guides.items():
        _atomic(d / (f'guide-{kind}.md' if kind else 'guide.md'), text)
    _atomic(d / 'profile.json', json.dumps(data, ensure_ascii=False, indent=1))
    return d / 'guide.md'


def clear_profile(profile: str = DEFAULT) -> None:
    """분석 결과 지우기 — 글이 3편 아래로 줄면 옛 안내서(뺀 글의 예문 포함)가 남지 않게."""
    d = profile_dir(profile, create=False)
    for p in [d / 'profile.json', d / 'guide.md', *d.glob('guide-*.md')]:
        p.unlink(missing_ok=True)


def load_profile(profile: str = DEFAULT) -> dict | None:
    pj = profile_dir(profile, create=False) / 'profile.json'
    try:
        data = json.loads(pj.read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return None  # 없거나 깨졌으면 다시 분석하게
    return data if isinstance(data, dict) else None


def load_guide(profile: str = DEFAULT, kind: str = '') -> str | None:
    p = profile_dir(profile, create=False) / (f'guide-{kind}.md' if kind else 'guide.md')
    try:
        return p.read_text(encoding='utf-8', errors='replace')
    except OSError:
        return None
