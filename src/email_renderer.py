"""Jinja2 기반 이메일 템플릿 렌더링 모듈."""
from __future__ import annotations

import os

from jinja2 import Environment, FileSystemLoader, Undefined


class _SilentUndefined(Undefined):
    """누락 변수를 빈 문자열로 처리."""

    def __str__(self) -> str:
        return ''

    def __iter__(self):
        return iter([])

    def __bool__(self) -> bool:
        return False


def render_email(template_path: str, context: dict) -> str:
    """HTML 템플릿에 변수를 치환해 렌더링된 HTML 반환.

    Args:
        template_path: Jinja2 템플릿 파일 경로
        context: 치환할 변수 딕셔너리

    Returns:
        렌더링된 HTML 문자열

    Raises:
        FileNotFoundError: 템플릿 파일 미존재 시
    """
    if not os.path.exists(template_path):
        raise FileNotFoundError(f'템플릿 파일을 찾을 수 없습니다: {template_path}')

    template_dir = os.path.dirname(os.path.abspath(template_path))
    template_name = os.path.basename(template_path)

    env = Environment(
        loader=FileSystemLoader(template_dir),
        undefined=_SilentUndefined,
    )
    template = env.get_template(template_name)
    return template.render(**context)
