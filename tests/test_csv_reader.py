"""csv_reader 모듈 테스트."""
from __future__ import annotations

import os
import tempfile

import pytest

from src.csv_reader import read_contacts


VALID_CSV = """name,email,company,position
김철수,chulsoo@example.com,ABC 주식회사,마케팅 팀장
이영희,younghee@example.com,XYZ 코퍼레이션,영업 이사
"""

MISSING_COLUMN_CSV = """name,company
김철수,ABC 주식회사
"""

INVALID_EMAIL_CSV = """name,email,company
홍길동,invalid-email,테스트 회사
김철수,chulsoo@example.com,ABC
"""

EMPTY_CSV = """name,email,company
"""

UTF8_SIG_CSV = "\ufeffname,email,company\n김철수,chulsoo@example.com,ABC\n"

MIXED_CSV = """name,email,company,position
김철수,chulsoo@example.com,ABC 주식회사,마케팅 팀장
홍길동,invalid-email,테스트 회사,테스터
이영희,younghee@example.com,XYZ 코퍼레이션,영업 이사
"""


def _write_tmp(content: str, encoding: str = 'utf-8') -> str:
    """임시 파일 생성 후 경로 반환."""
    fd, path = tempfile.mkstemp(suffix='.csv')
    with os.fdopen(fd, 'w', encoding=encoding) as f:
        f.write(content)
    return path


class TestReadContacts:
    def test_valid_csv_parses_successfully(self):
        path = _write_tmp(VALID_CSV)
        try:
            valid, invalid = read_contacts(path)
            assert len(valid) == 2
            assert len(invalid) == 0
            assert valid[0]['name'] == '김철수'
            assert valid[0]['email'] == 'chulsoo@example.com'
        finally:
            os.unlink(path)

    def test_missing_required_column_raises_value_error(self):
        path = _write_tmp(MISSING_COLUMN_CSV)
        try:
            with pytest.raises(ValueError, match='email'):
                read_contacts(path)
        finally:
            os.unlink(path)

    def test_invalid_email_filtered_to_invalid_rows(self):
        path = _write_tmp(INVALID_EMAIL_CSV)
        try:
            valid, invalid = read_contacts(path)
            assert len(valid) == 1
            assert len(invalid) == 1
            assert valid[0]['email'] == 'chulsoo@example.com'
            assert invalid[0]['email'] == 'invalid-email'
        finally:
            os.unlink(path)

    def test_empty_csv_returns_empty_lists(self):
        path = _write_tmp(EMPTY_CSV)
        try:
            valid, invalid = read_contacts(path)
            assert valid == []
            assert invalid == []
        finally:
            os.unlink(path)

    def test_utf8_sig_encoding_handled(self):
        path = _write_tmp(UTF8_SIG_CSV, encoding='utf-8-sig')
        try:
            valid, invalid = read_contacts(path)
            assert len(valid) == 1
            assert valid[0]['name'] == '김철수'
        finally:
            os.unlink(path)

    def test_mixed_valid_invalid_separation(self):
        path = _write_tmp(MIXED_CSV)
        try:
            valid, invalid = read_contacts(path)
            assert len(valid) == 2
            assert len(invalid) == 1
            emails = [r['email'] for r in valid]
            assert 'chulsoo@example.com' in emails
            assert 'younghee@example.com' in emails
        finally:
            os.unlink(path)

    def test_file_not_found_raises(self):
        with pytest.raises(FileNotFoundError):
            read_contacts('/nonexistent/path/contacts.csv')
