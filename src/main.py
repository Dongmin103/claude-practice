"""CLI 진입점 - CSV 기반 맞춤형 이메일 자동화 시스템."""
from __future__ import annotations

import argparse
import html
import os
import re
import sys

from dotenv import load_dotenv

from src.csv_reader import read_contacts
from src.email_renderer import render_email
from src.email_sender import send_email, validate_smtp_config
from src.logger import log_result

_TAG_RE = re.compile(r'<[^>]+>')

DEFAULT_CSV = 'data/contacts.csv'
DEFAULT_TEMPLATE = 'templates/email_template.html'
DEFAULT_LOG = 'logs/send_log.csv'
EMAIL_SUBJECT = '안녕하세요, 서비스 소개 드립니다'


def parse_args() -> argparse.Namespace:
    """CLI 인자 파싱."""
    parser = argparse.ArgumentParser(description='CSV 기반 맞춤형 이메일 자동화')
    parser.add_argument('--csv', default=DEFAULT_CSV, help='연락처 CSV 파일 경로')
    parser.add_argument('--template', default=DEFAULT_TEMPLATE, help='이메일 HTML 템플릿 경로')
    parser.add_argument('--log', default=DEFAULT_LOG, help='결과 로그 CSV 경로')
    parser.add_argument('--dry-run', action='store_true', help='실제 발송 없이 미리보기만')
    return parser.parse_args()


def main() -> None:
    """메인 실행 함수."""
    load_dotenv()
    args = parse_args()

    # 환경변수 검증 (dry-run도 동일 검증)
    try:
        validate_smtp_config()
    except ValueError as e:
        print(f'[오류] {e}', file=sys.stderr)
        sys.exit(1)

    # CSV 읽기
    try:
        valid_rows, invalid_rows = read_contacts(args.csv)
    except (FileNotFoundError, ValueError) as e:
        print(f'[오류] {e}', file=sys.stderr)
        sys.exit(1)

    if invalid_rows:
        print(f'[경고] 잘못된 이메일 {len(invalid_rows)}건 건너뜀:')
        for row in invalid_rows:
            print(f'  - {row.get("name", "?")} <{row.get("email", "?")}>')

    if not valid_rows:
        print('발송할 유효한 연락처가 없습니다.')
        sys.exit(0)

    # 발송 확인
    mode_label = '[DRY-RUN] ' if args.dry_run else ''
    while True:
        print(f'\n{mode_label}{len(valid_rows)}명에게 발송합니다. 계속할까요? (y/n): ', end='')
        answer = input().strip().lower()
        if answer in ('y', 'n'):
            break
        print('y 또는 n을 입력해주세요.')
    if answer != 'y':
        print('취소되었습니다.')
        sys.exit(0)

    # 로그 디렉토리 생성
    log_dir = os.path.dirname(args.log)
    if log_dir:
        os.makedirs(log_dir, exist_ok=True)

    # 발송
    success_count = 0
    failure_count = 0

    for row in valid_rows:
        email = row['email']
        name = row.get('name', '')

        try:
            html_body = render_email(args.template, row)
        except FileNotFoundError as e:
            print(f'[오류] 템플릿 파일 없음: {e}', file=sys.stderr)
            sys.exit(1)

        if args.dry_run:
            plain_preview = _TAG_RE.sub('', html.unescape(html_body))[:300].strip()
            print(f'\n--- {name} <{email}> 미리보기 ---')
            print(plain_preview)
            print('---')
            log_result(args.log, email, 'success')
            success_count += 1
            continue

        ok = send_email(to_email=email, subject=EMAIL_SUBJECT, html_body=html_body)
        if ok:
            print(f'[성공] {name} <{email}>')
            log_result(args.log, email, 'success')
            success_count += 1
        else:
            print(f'[실패] {name} <{email}>')
            log_result(args.log, email, 'failure', 'SMTP 발송 실패')
            failure_count += 1

    print(f'\n완료: 성공 {success_count}건 / 실패 {failure_count}건')
    print(f'로그: {args.log}')


if __name__ == '__main__':
    main()
