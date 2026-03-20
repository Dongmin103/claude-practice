"""SMTP 이메일 발송 모듈."""
from __future__ import annotations

import os
import smtplib
import time
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

REQUIRED_ENV_VARS = ('SMTP_HOST', 'SMTP_PORT', 'SMTP_USER', 'SMTP_PASSWORD', 'SENDER_EMAIL')
MAX_RETRIES = 3
RETRY_INTERVAL = 1  # seconds


def send_email(
    to_email: str,
    subject: str,
    html_body: str,
    dry_run: bool = False,
) -> bool:
    """이메일 발송.

    Args:
        to_email: 수신자 이메일 주소
        subject: 이메일 제목
        html_body: HTML 본문
        dry_run: True이면 실제 발송 없이 미리보기만

    Returns:
        발송 성공 여부 (dry_run은 항상 True)

    Raises:
        ValueError: 환경변수 미설정 시
    """
    config = _load_smtp_config()

    if dry_run:
        return True

    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = config['sender_email']
    msg['To'] = to_email
    msg.attach(MIMEText(html_body, 'html', 'utf-8'))

    try:
        port = int(config['port'])
    except ValueError:
        raise ValueError(f'SMTP_PORT가 유효한 숫자가 아닙니다: {config["port"]}')

    last_error: Exception | None = None
    for attempt in range(MAX_RETRIES):
        try:
            with smtplib.SMTP(config['host'], port) as server:
                server.starttls()
                server.login(config['user'], config['password'])
                server.sendmail(config['sender_email'], to_email, msg.as_string())
            return True
        except smtplib.SMTPAuthenticationError:
            raise  # 인증 실패는 재시도 불필요
        except smtplib.SMTPException as e:
            last_error = e
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_INTERVAL)
        except OSError as e:
            last_error = e
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_INTERVAL)

    return False


def validate_smtp_config() -> None:
    """SMTP 환경변수 설정 여부만 검증 (로드 없이).

    Raises:
        ValueError: 필수 환경변수 미설정 시
    """
    _load_smtp_config()


def _load_smtp_config() -> dict:
    """환경변수에서 SMTP 설정 로드.

    Raises:
        ValueError: 필수 환경변수 미설정 시
    """
    missing = [var for var in REQUIRED_ENV_VARS if not os.environ.get(var)]
    if missing:
        raise ValueError(f'환경변수 미설정: {", ".join(missing)}')

    return {
        'host': os.environ['SMTP_HOST'],
        'port': os.environ['SMTP_PORT'],
        'user': os.environ['SMTP_USER'],
        'password': os.environ['SMTP_PASSWORD'],
        'sender_email': os.environ['SENDER_EMAIL'],
    }
