"""logger 모듈 테스트."""
from __future__ import annotations

import csv
import os
import tempfile

import pytest

from src.logger import log_result


class TestLogResult:
    def _read_log(self, path: str) -> list[dict]:
        with open(path, 'r', encoding='utf-8', newline='') as f:
            return list(csv.DictReader(f))

    def test_success_log_saved(self):
        fd, path = tempfile.mkstemp(suffix='.csv')
        os.close(fd)
        os.unlink(path)  # 파일 없는 상태에서 시작
        try:
            log_result(path, 'user@example.com', 'success')
            rows = self._read_log(path)
            assert len(rows) == 1
            assert rows[0]['email'] == 'user@example.com'
            assert rows[0]['status'] == 'success'
            assert rows[0]['error_message'] == ''
            assert rows[0]['timestamp'] != ''
        finally:
            if os.path.exists(path):
                os.unlink(path)

    def test_failure_log_includes_error_message(self):
        fd, path = tempfile.mkstemp(suffix='.csv')
        os.close(fd)
        os.unlink(path)
        try:
            log_result(path, 'bad@example.com', 'failure', 'SMTP 연결 실패')
            rows = self._read_log(path)
            assert len(rows) == 1
            assert rows[0]['status'] == 'failure'
            assert rows[0]['error_message'] == 'SMTP 연결 실패'
        finally:
            if os.path.exists(path):
                os.unlink(path)

    def test_append_to_existing_log(self):
        fd, path = tempfile.mkstemp(suffix='.csv')
        os.close(fd)
        os.unlink(path)
        try:
            log_result(path, 'first@example.com', 'success')
            log_result(path, 'second@example.com', 'failure', '오류 발생')
            log_result(path, 'third@example.com', 'success')
            rows = self._read_log(path)
            assert len(rows) == 3
            assert rows[0]['email'] == 'first@example.com'
            assert rows[1]['email'] == 'second@example.com'
            assert rows[2]['email'] == 'third@example.com'
        finally:
            if os.path.exists(path):
                os.unlink(path)

    def test_log_has_required_columns(self):
        fd, path = tempfile.mkstemp(suffix='.csv')
        os.close(fd)
        os.unlink(path)
        try:
            log_result(path, 'user@example.com', 'success')
            with open(path, 'r', encoding='utf-8', newline='') as f:
                reader = csv.DictReader(f)
                columns = reader.fieldnames or []
            assert 'email' in columns
            assert 'status' in columns
            assert 'timestamp' in columns
            assert 'error_message' in columns
        finally:
            if os.path.exists(path):
                os.unlink(path)
