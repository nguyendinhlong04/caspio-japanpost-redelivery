"""
Định nghĩa hằng số & đọc biến môi trường cần thiết.
Raise lỗi sớm nếu thiếu để CI thất bại ngay.
"""
import os
from typing import Final

CASPIO_BASE_URL: Final   = 'https://d2hbz700.caspio.com'
CASPIO_TABLE_NAME: Final = 'DonHang'


def _env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"⚠️  Missing required environment variable: '{name}'")
    return value


CASPIO_CLIENT_ID:     Final = _env('CASPIO_CLIENT_ID')
CASPIO_CLIENT_SECRET: Final = _env('CASPIO_CLIENT_SECRET')
