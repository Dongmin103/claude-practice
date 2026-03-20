"""email_renderer 모듈 테스트."""
from __future__ import annotations

import os
import tempfile

import pytest

from src.email_renderer import render_email


TEMPLATE_CONTENT = """<!DOCTYPE html>
<html>
<body>
  <h2>안녕하세요, {{ name }}님</h2>
  <p>{{ company }}의 {{ position }} 직책을 맡고 계신 것으로 알고 있습니다.</p>
</body>
</html>"""


def _write_tmp_template(content: str) -> str:
    fd, path = tempfile.mkstemp(suffix='.html')
    with os.fdopen(fd, 'w', encoding='utf-8') as f:
        f.write(content)
    return path


class TestRenderEmail:
    def test_variable_substitution_works(self):
        path = _write_tmp_template(TEMPLATE_CONTENT)
        try:
            context = {'name': '김철수', 'company': 'ABC 주식회사', 'position': '마케팅 팀장'}
            result = render_email(path, context)
            assert '김철수님' in result
            assert 'ABC 주식회사' in result
            assert '마케팅 팀장' in result
        finally:
            os.unlink(path)

    def test_missing_variable_replaced_with_empty_string(self):
        path = _write_tmp_template(TEMPLATE_CONTENT)
        try:
            # position 변수를 context에서 제외
            context = {'name': '김철수', 'company': 'ABC 주식회사'}
            result = render_email(path, context)
            # 예외 없이 렌더링되어야 함
            assert '김철수님' in result
            # 누락 변수는 빈 문자열로 처리
            assert '{{ position }}' not in result
        finally:
            os.unlink(path)

    def test_template_file_not_found_raises(self):
        with pytest.raises(FileNotFoundError):
            render_email('/nonexistent/template.html', {'name': '테스트'})

    def test_returns_string(self):
        path = _write_tmp_template(TEMPLATE_CONTENT)
        try:
            result = render_email(path, {'name': '테스트', 'company': '회사', 'position': '직책'})
            assert isinstance(result, str)
            assert len(result) > 0
        finally:
            os.unlink(path)

    def test_empty_context_no_exception(self):
        path = _write_tmp_template(TEMPLATE_CONTENT)
        try:
            result = render_email(path, {})
            assert isinstance(result, str)
        finally:
            os.unlink(path)
