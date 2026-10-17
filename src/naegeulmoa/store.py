"""내 글 보관 — 모든 것은 내 컴퓨터(~/.naegeulmoa 또는 NAEGEULMOA_HOME)에만 둔다. 어디로도 보내지 않는다.

폴더 모양:
  <집>/<문체 이름>/samples/0001.txt …   내가 쓴 글(한 편 = 파일 하나, 첫 줄 「# 제목」)
  <집>/<문체 이름>/profile.json         분석 수치
  <집>/<문체 이름>/guide.md             AI 에게 주는 문체 안내서
"""
from __future__ import annotations

import json
import os
import re
from pathlib import Path

DEFAULT = '기본'


def home() -> Path:
    return Path(os.environ.get('NAEGEULMOA_HOME', Path.home() / '.naegeulmoa'))


def _safe(name: str) -> str:
    name = (name or DEFAULT).strip()
    if not re.fullmatch(r'[0-9A-Za-z가-힣 _\-]{1,40}', name):
        raise ValueError('문체 이름은 한글 · 영문 · 숫자 · 띄어쓰기 · _ - 로 40자 안에서 지어 주세요.')
    return name


def profile_dir(profile: str = DEFAULT) -> Path:
    d = home() / _safe(profile)
    (d / 'samples').mkdir(parents=True, exist_ok=True)
    return d


def add_sample(text: str, title: str = '', profile: str = DEFAULT) -> str:
    text = text.strip()
    if len(re.sub(r'\s', '', text)) < 100:
        raise ValueError('글이 너무 짧습니다. 100자 이상인 글을 넣어 주세요(문체를 읽으려면 문장이 여러 개 있어야 합니다).')
    d = profile_dir(profile) / 'samples'
    nums = [int(p.stem) for p in d.glob('*.txt') if p.stem.isdigit()]
    sid = f'{(max(nums) + 1) if nums else 1:04d}'
    head = f'# {title.strip()}\n' if title.strip() else ''
    (d / f'{sid}.txt').write_text(head + text + '\n', encoding='utf-8')
    return sid


def read_sample(path: Path) -> tuple[str, str]:
    raw = path.read_text(encoding='utf-8')
    if raw.startswith('# '):
        title, _, body = raw.partition('\n')
        return title[2:].strip(), body.strip()
    return '', raw.strip()


def samples(profile: str = DEFAULT) -> list[tuple[str, str, str]]:
    """(번호, 제목, 본문) 목록."""
    d = profile_dir(profile) / 'samples'
    out = []
    for p in sorted(d.glob('*.txt')):
        title, body = read_sample(p)
        out.append((p.stem, title, body))
    return out


def remove_sample(sid: str, profile: str = DEFAULT) -> bool:
    p = profile_dir(profile) / 'samples' / f'{sid}.txt'
    if p.exists():
        p.unlink()
        return True
    return False


def profiles() -> list[str]:
    h = home()
    return sorted(p.name for p in h.iterdir() if p.is_dir()) if h.exists() else []


def save_profile(data: dict, guide: str, profile: str = DEFAULT) -> Path:
    d = profile_dir(profile)
    (d / 'profile.json').write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding='utf-8')
    (d / 'guide.md').write_text(guide, encoding='utf-8')
    return d / 'guide.md'


def load_profile(profile: str = DEFAULT) -> tuple[dict | None, str | None]:
    d = profile_dir(profile)
    pj, gm = d / 'profile.json', d / 'guide.md'
    if not pj.exists():
        return None, None
    return json.loads(pj.read_text(encoding='utf-8')), gm.read_text(encoding='utf-8') if gm.exists() else None
