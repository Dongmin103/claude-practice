"""main.py 통합 테스트."""
from __future__ import annotations

import os
import sys
from io import StringIO
from unittest.mock import MagicMock, call, patch

import pytest

SMTP_ENV = {
    'SMTP_HOST': 'smtp.example.com',
    'SMTP_PORT': '587',
    'SMTP_USER': 'user@example.com',
    'SMTP_PASSWORD': 'secret',
    'SENDER_EMAIL': 'sender@example.com',
}

VALID_ROWS = [
    {'name': '김철수', 'email': 'chulsoo@example.com', 'company': 'ABC'},
    {'name': '이영희', 'email': 'younghee@example.com', 'company': 'XYZ'},
]


def _run_main(argv: list[str], user_input: str = 'y') -> int:
    """main()을 실행하고 exit code를 반환."""
    with patch('sys.argv', ['main.py'] + argv):
        with patch('builtins.input', return_value=user_input):
            from src.main import main
            try:
                main()
                return 0
            except SystemExit as e:
                return int(e.code) if e.code is not None else 0


class TestMainDryRun:
    def test_dry_run_success(self, tmp_path, capsys):
        log_path = str(tmp_path / 'log.csv')
        template_path = 'templates/email_template.html'

        with patch.dict(os.environ, SMTP_ENV):
            with patch('src.main.read_contacts', return_value=(VALID_ROWS, [])):
                with patch('src.main.render_email', return_value='<p>안녕하세요</p>'):
                    with patch('src.main.log_result') as mock_log:
                        code = _run_main(
                            ['--dry-run', '--log', log_path, '--template', template_path]
                        )

        assert code == 0
        assert mock_log.call_count == 2
        captured = capsys.readouterr()
        assert '미리보기' in captured.out

    def test_dry_run_shows_plain_text_not_html(self, tmp_path, capsys):
        log_path = str(tmp_path / 'log.csv')
        with patch.dict(os.environ, SMTP_ENV):
            with patch('src.main.read_contacts', return_value=(VALID_ROWS[:1], [])):
                with patch('src.main.render_email', return_value='<h2>안녕하세요</h2>'):
                    with patch('src.main.log_result'):
                        _run_main(['--dry-run', '--log', log_path])

        captured = capsys.readouterr()
        assert '<h2>' not in captured.out  # HTML 태그 미출력 확인


class TestMainSend:
    def test_send_success(self, tmp_path, capsys):
        log_path = str(tmp_path / 'log.csv')
        with patch.dict(os.environ, SMTP_ENV):
            with patch('src.main.read_contacts', return_value=(VALID_ROWS, [])):
                with patch('src.main.render_email', return_value='<p>본문</p>'):
                    with patch('src.main.send_email', return_value=True):
                        with patch('src.main.log_result') as mock_log:
                            code = _run_main(['--log', log_path])

        assert code == 0
        assert mock_log.call_count == 2
        captured = capsys.readouterr()
        assert '성공' in captured.out

    def test_send_failure_logged(self, tmp_path, capsys):
        log_path = str(tmp_path / 'log.csv')
        with patch.dict(os.environ, SMTP_ENV):
            with patch('src.main.read_contacts', return_value=(VALID_ROWS[:1], [])):
                with patch('src.main.render_email', return_value='<p>본문</p>'):
                    with patch('src.main.send_email', return_value=False):
                        with patch('src.main.log_result') as mock_log:
                            code = _run_main(['--log', log_path])

        assert code == 0
        mock_log.assert_called_once_with(
            log_path, VALID_ROWS[0]['email'], 'failure', 'SMTP 발송 실패'
        )


class TestMainEdgeCases:
    def test_user_cancels(self, tmp_path):
        log_path = str(tmp_path / 'log.csv')
        with patch.dict(os.environ, SMTP_ENV):
            with patch('src.main.read_contacts', return_value=(VALID_ROWS, [])):
                with patch('src.main.send_email') as mock_send:
                    code = _run_main(['--log', log_path], user_input='n')

        assert code == 0
        mock_send.assert_not_called()

    def test_missing_env_exits(self, tmp_path):
        log_path = str(tmp_path / 'log.csv')
        clean_env = {k: v for k, v in os.environ.items() if k not in SMTP_ENV}
        with patch.dict(os.environ, clean_env, clear=True):
            code = _run_main(['--log', log_path])
        assert code == 1

    def test_invalid_csv_exits(self, tmp_path):
        log_path = str(tmp_path / 'log.csv')
        with patch.dict(os.environ, SMTP_ENV):
            with patch('src.main.read_contacts', side_effect=FileNotFoundError('없음')):
                code = _run_main(['--log', log_path])
        assert code == 1

    def test_no_valid_rows_exits(self, tmp_path):
        log_path = str(tmp_path / 'log.csv')
        with patch.dict(os.environ, SMTP_ENV):
            with patch('src.main.read_contacts', return_value=([], [])):
                code = _run_main(['--log', log_path])
        assert code == 0

    def test_invalid_rows_warning_shown(self, tmp_path, capsys):
        log_path = str(tmp_path / 'log.csv')
        invalid = [{'name': '홍길동', 'email': 'bad'}]
        with patch.dict(os.environ, SMTP_ENV):
            with patch('src.main.read_contacts', return_value=([], invalid)):
                _run_main(['--log', log_path])
        captured = capsys.readouterr()
        assert '경고' in captured.out

    def test_template_not_found_exits(self, tmp_path):
        log_path = str(tmp_path / 'log.csv')
        with patch.dict(os.environ, SMTP_ENV):
            with patch('src.main.read_contacts', return_value=(VALID_ROWS[:1], [])):
                with patch('src.main.render_email', side_effect=FileNotFoundError('없음')):
                    code = _run_main(['--log', log_path])
        assert code == 1

    def test_invalid_input_loops_until_valid(self, tmp_path):
        log_path = str(tmp_path / 'log.csv')
        inputs = iter(['x', 'z', 'n'])
        with patch.dict(os.environ, SMTP_ENV):
            with patch('src.main.read_contacts', return_value=(VALID_ROWS, [])):
                with patch('builtins.input', side_effect=inputs):
                    with patch('src.main.send_email') as mock_send:
                        with patch('sys.argv', ['main.py', '--log', log_path]):
                            from src.main import main
                            try:
                                main()
                            except SystemExit:
                                pass
        mock_send.assert_not_called()
