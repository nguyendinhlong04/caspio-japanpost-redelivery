from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from selenium import webdriver

from .caspio_api import update_order
from .japanpost import open_and_fill

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def process_orders(orders: list[dict], token: str) -> None:
    driver: webdriver.Chrome | None = None
    tz = timezone(timedelta(hours=9))
    today = datetime.now(tz).date()

    try:
        total_orders = len(orders)
        processed_count = 0

        for index, order in enumerate(orders):
            order_id = order.get('ID', 'N/A')
            logging.info("=====================================================================")
            logging.info(f"BẮT ĐẦU KIỂM TRA ĐƠN HÀNG {index + 1}/{total_orders} (ID: {order_id})")
            logging.info(f"[DEBUG] Dữ liệu thô của đơn hàng ID={order_id}: {order}")

            try:
                # -- Điều kiện 1: Tình trạng vận chuyển --
                if order.get('tinh_trang_van_chuyen') != "Vắng nhà":
                    logging.warning(f"   → Bỏ qua ID={order_id} vì 'tinh_trang_van_chuyen' là '{order.get('tinh_trang_van_chuyen')}'")
                    continue
                logging.info(f"[OK] ID={order_id} thỏa mãn điều kiện 'tinh_trang_van_chuyen'.")

                # -- Điều kiện 2: Đơn vị vận chuyển --
                if order.get('don_vi_van_chuyen') != "JapanPost":
                    logging.warning(f"   → Bỏ qua ID={order_id} vì 'don_vi_van_chuyen' là '{order.get('don_vi_van_chuyen')}'")
                    continue
                logging.info(f"[OK] ID={order_id} thỏa mãn điều kiện 'don_vi_van_chuyen'.")

                # -- Điều kiện 3: Ngày hẹn lại --
                reschedule_date_str = order.get('ngayhenlai')
                should_process = True
                if reschedule_date_str and str(reschedule_date_str).lower() != "nan":
                    try:
                        reschedule_date = datetime.fromisoformat(reschedule_date_str.split("T")[0]).date()
                        if reschedule_date >= today:
                            logging.info(f"   → Bỏ qua ID={order_id} vì đã được hẹn lại vào ngày {reschedule_date} (>= hôm nay)")
                            should_process = False
                    except (ValueError, TypeError):
                        logging.warning(f"   → Không thể phân tích 'ngayhenlai' cho ID={order_id}. Giá trị: '{reschedule_date_str}'. Vẫn tiếp tục xử lý.")
                
                if not should_process:
                    continue
                logging.info(f"[OK] ID={order_id} thỏa mãn điều kiện 'ngayhenlai'.")


                # -- Điều kiện 4: Thông tin cần thiết --
                link = order.get('LinkVanChuyen')
                khung_gio = order.get('khung_gio_giao')
                if not all([link, khung_gio, order_id != 'N/A']):
                    logging.warning(f"   → Bỏ qua ID={order_id} vì thiếu thông tin. LinkVanChuyen: '{link}', khung_gio_giao: '{khung_gio}', ID: '{order_id}'")
                    continue
                logging.info(f"[OK] ID={order_id} có đủ thông tin cần thiết.")

                # -- Bắt đầu xử lý Selenium --
                if driver is None:
                    logging.info("Khởi tạo trình duyệt Selenium (headless mode)...")
                    opts = webdriver.ChromeOptions()
                    opts.add_argument("--headless=new")
                    opts.add_argument("--no-sandbox")
                    opts.add_argument("--disable-dev-shm-usage")
                    driver = webdriver.Chrome(options=opts)

                logging.info(f">> Bắt đầu xử lý Selenium cho ID={order_id}, Khung giờ={khung_gio}")

                first_day_selected = open_and_fill(driver, link, khung_gio, order, order_id)

                logging.info(f"[ID={order_id}] Đặt lịch thành công trên web. Tiến hành cập nhật Caspio.")
                update_order(token, order_id, first_day_selected)

                processed_count += 1
                logging.info(f"KẾT THÚC XỬ LÝ ID={order_id} THÀNH CÔNG")

            except Exception as e:
                logging.error(f"LỖI NGHIÊM TRỌNG khi xử lý ID={order_id}: {e}", exc_info=True)
                # Ghi lại lỗi nhưng vẫn tiếp tục với đơn hàng tiếp theo
                continue

        logging.info("=====================================================================")
        logging.info(f"Hoàn tất quá trình quét. Đã xử lý thành công {processed_count}/{total_orders} đơn hàng.")

    finally:
        if driver is not None:
            logging.info("Đóng trình duyệt Selenium...")
            driver.quit()
