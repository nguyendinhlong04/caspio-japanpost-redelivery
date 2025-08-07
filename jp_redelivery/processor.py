"""
Quét danh sách đơn, gọi Selenium và cập nhật Caspio.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from selenium import webdriver

from .japanpost import open_and_fill
from .caspio_api import update_order


def process_orders(orders: list[dict], token: str) -> None:
    driver: webdriver.Chrome | None = None
    tz = timezone(timedelta(hours=9))
    today = datetime.now(tz).date()

    for order in orders:
        if order.get('tinh_trang_van_chuyen') != "Vắng nhà":
            continue
        if order.get('don_vi_van_chuyen') != "JapanPost":
            continue

        nhl = order.get('ngayhenlai')
        if nhl and str(nhl).lower() != "nan":
            try:
                if datetime.fromisoformat(nhl.split("T")[0]).date() >= today:
                    continue
            except Exception:
                pass

        link = order.get('LinkVanChuyen')
        khung = order.get('khung_gio_giao')
        idv = order.get('ID')
        if not all([link, khung, idv]):
            continue

        if driver is None:
            opts = webdriver.ChromeOptions()
            opts.add_argument("--headless=new")
            chrome_bin = os.getenv("CHROME_BIN", "/usr/bin/chromium-browser")
            opts.binary_location = chrome_bin
            driver = webdriver.Chrome(options=opts)

        print(f">> Xử lý ID={idv}, slot={khung}")
        first = open_and_fill(driver, link, khung, order)
        update_order(token, idv, first)

    if driver is not None:
        driver.quit()
