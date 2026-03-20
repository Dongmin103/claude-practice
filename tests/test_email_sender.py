"""email_sender 모듈 테스트."""
from __future__ import annotations

import os
import smtplib
from unittest.mock import MagicMock, patch

import pytest

from src.email_sender import send_email

SMTP_ENV = {
    'SMTP_HOST': 'smtp.example.com',
    'SMTP_PORT': '587',
    'SMTP_USER': 'user@example.com',
    'SMTP_PASSWORD': 'secret',
    'SENDER_EMAIL': 'sender@example.com',
}


class TestSendEmail:
    def test_smtp_connection_and_send_success(self):
        with patch.dict(os.environ, SMTP_ENV):
            with patch('smtplib.SMTP') as mock_smtp_class:
                mock_smtp = MagicMock()
                mock_smtp_class.return_value.__enter__ = MagicMock(return_value=mock_smtp)
                mock_smtp_class.return_value.__exit__ = MagicMock(return_value=False)

                result = send_email(
                    to_email='to@example.com',
                    subject='테스트',
                    html_body='<p>테스트</p>',
                )
                assert result is True

    def test_send_failure_retries_three_times(self):
        with patch.dict(os.environ, SMTP_ENV):
            with patch('smtplib.SMTP') as mock_smtp_class:
                with patch('time.sleep'):
                    mock_smtp = MagicMock()
                    mock_smtp_class.return_value.__enter__ = MagicMock(return_value=mock_smtp)
                    mock_smtp_class.return_value.__exit__ = MagicMock(return_value=False)
                    mock_smtp.sendmail.side_effect = smtplib.SMTPException('연결 오류')

                    result = send_email(
                        to_email='to@example.com',
                        subject='테스트',
                        html_body='<p>테스트</p>',
                    )
                    assert result is False
                    assert mock_smtp.sendmail.call_count == 3

    def test_missing_env_var_raises_value_error(self):
        # 환경변수를 모두 제거한 상태에서 테스트
        env_without_smtp = {k: v for k, v in os.environ.items()
                            if k not in SMTP_ENV}
        with patch.dict(os.environ, env_without_smtp, clear=True):
            with pytest.raises(ValueError):
                send_email(
                    to_email='to@example.com',
                    subject='테스트',
                    html_body='<p>테스트</p>',
                )

    def test_dry_run_does_not_send(self):
        with patch.dict(os.environ, SMTP_ENV):
            with patch('smtplib.SMTP') as mock_smtp_class:
                result = send_email(
                    to_email='to@example.com',
                    subject='테스트',
                    html_body='<p>테스트</p>',
                    dry_run=True,
                )
                assert result is True
                mock_smtp_class.assert_not_called()

    def test_dry_run_missing_env_still_raises(self):
        env_without_smtp = {k: v for k, v in os.environ.items()
                            if k not in SMTP_ENV}
        with patch.dict(os.environ, env_without_smtp, clear=True):
            with pytest.raises(ValueError):
                send_email(
                    to_email='to@example.com',
                    subject='테스트',
                    html_body='<p>테스트</p>',
                    dry_run=True,
                )
