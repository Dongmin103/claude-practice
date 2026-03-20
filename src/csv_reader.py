"""CSV 파싱 및 검증 모듈."""
from __future__ import annotations

import re
from typing import Tuple

import pandas as pd

EMAIL_PATTERN = re.compile(r'^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$')
REQUIRED_COLUMNS = {'name', 'email'}


def read_contacts(filepath: str) -> Tuple[list[dict], list[dict]]:
    """CSV 파일을 읽어 유효/무효 행을 분리 반환.

    Args:
        filepath: CSV 파일 경로

    Returns:
        (valid_rows, invalid_rows) 튜플

    Raises:
        ValueError: 필수 컬럼(name, email) 누락 시
        FileNotFoundError: 파일 미존재 시
    """
    try:
        df = pd.read_csv(filepath, encoding='utf-8-sig')
    except FileNotFoundError:
        raise FileNotFoundError(f'파일을 찾을 수 없습니다: {filepath}')

    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        raise ValueError(f'필수 컬럼 누락: {", ".join(sorted(missing))}')

    if df.empty:
        return [], []

    valid_mask = df['email'].apply(_is_valid_email)
    valid_rows = df[valid_mask].to_dict(orient='records')
    invalid_rows = df[~valid_mask].to_dict(orient='records')

    return valid_rows, invalid_rows


def _is_valid_email(email: str) -> bool:
    """이메일 형식 검증."""
    if not isinstance(email, str):
        return False
    return bool(EMAIL_PATTERN.match(email.strip()))
