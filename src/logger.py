"""발송 결과 CSV 로깅 모듈."""
from __future__ import annotations

import csv
import os
from datetime import datetime, timezone

LOG_COLUMNS = ('email', 'status', 'timestamp', 'error_message')


def log_result(
    log_path: str,
    email: str,
    status: str,
    error_message: str = '',
) -> None:
    """발송 결과를 CSV에 append 저장.

    Args:
        log_path: 로그 CSV 파일 경로
        email: 수신자 이메일
        status: 'success' 또는 'failure'
        error_message: 실패 시 오류 메시지
    """
    file_exists = os.path.exists(log_path)
    timestamp = datetime.now(tz=timezone.utc).isoformat()

    with open(log_path, 'a', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=LOG_COLUMNS)
        if not file_exists:
            writer.writeheader()
        writer.writerow({
            'email': email,
            'status': status,
            'timestamp': timestamp,
            'error_message': error_message,
        })
