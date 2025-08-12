"""
Quét danh sách đơn, gọi Selenium và cập nhật Caspio.
Phiên bản nâng cấp với logging và xử lý lỗi bền bỉ.
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from selenium import webdriver

from .caspio_api import update_order
from .japanpost import open_and_fill

# Cấu hình logging cơ bản
# Thêm format để log trông rõ ràng hơn với timestamp, level và message
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def process_orders(orders: list[dict], token: str) -> None:
    """
    Xử lý danh sách đơn hàng được cung cấp.

    Args:
        orders: Danh sách các đơn hàng từ Caspio.
        token: Access token để xác thực với Caspio API.
    """
    driver: webdriver.Chrome | None = None
    tz = timezone(timedelta(hours=9))  # Múi giờ Nhật Bản (JST)
    today = datetime.now(tz).date()

    try:
        total_orders = len(orders)
        processed_count = 0

        for index, order in enumerate(orders):
            # Lấy ID đơn hàng sớm để ghi log lỗi nếu có
            order_id = order.get('ID', 'N/A')
            logging.info(f"Kiểm tra đơn hàng {index + 1}/{total_orders} (ID: {order_id})")

            try:
                # --- Bắt đầu logic lọc (giữ nguyên như cũ) ---
                if order.get('tinh_trang_van_chuyen') != "Vắng nhà":
                    continue

                if order.get('don_vi_van_chuyen') != "JapanPost":
                    continue

                # Kiểm tra ngày hẹn lại một cách an toàn hơn
                reschedule_date_str = order.get('ngayhenlai')
                if reschedule_date_str and str(reschedule_date_str).lower() != "nan":
                    try:
                        # Chỉ lấy phần ngày (YYYY-MM-DD) từ chuỗi ISO 8601
                        reschedule_date = datetime.fromisoformat(reschedule_date_str.split("T")[0]).date()
                        if reschedule_date >= today:
                            logging.info(f"   → Bỏ qua ID={order_id} vì đã được hẹn lại vào ngày {reschedule_date}")
                            continue
                    except (ValueError, TypeError):
                        # Bỏ qua nếu định dạng ngày không hợp lệ, coi như chưa hẹn lại
                        logging.warning(f"   → Không thể phân tích 'ngayhenlai' cho ID={order_id}. Giá trị: '{reschedule_date_str}'. Tiếp tục xử lý.")
                        pass

                # Kiểm tra các trường dữ liệu cần thiết
                link = order.get('LinkVanChuyen')
                khung_gio = order.get('khung_gio_giao')
                if not all([link, khung_gio, order_id != 'N/A']):
                    logging.warning(f"   → Bỏ qua ID={order_id} vì thiếu thông tin cần thiết (link, khung giờ hoặc ID).")
                    continue
                # --- Kết thúc logic lọc ---


                # Khởi tạo trình duyệt một cách lười biếng (chỉ khi có đơn hàng hợp lệ đầu tiên)
                if driver is None:
                    logging.info("Khởi tạo trình duyệt Selenium (headless mode)...")
                    opts = webdriver.ChromeOptions()
                    opts.add_argument("--headless=new")
                    # Một vài tùy chọn hữu ích khác để chạy ổn định trên server
                    opts.add_argument("--no-sandbox")
                    opts.add_argument("--disable-dev-shm-usage")
                    driver = webdriver.Chrome(options=opts)

                # Bắt đầu xử lý nghiệp vụ
                logging.info(f">> Bắt đầu xử lý ID={order_id}, Khung giờ={khung_gio}")
                
                # Gọi Selenium để điền form
                first_day_selected = open_and_fill(driver, link, khung_gio, order)
                
                # Cập nhật trạng thái trên Caspio
                update_order(token, order_id, first_day_selected)
                
                processed_count += 1

            except Exception as e:
                # Ghi lại lỗi của một đơn hàng cụ thể và tiếp tục với các đơn hàng khác
                logging.error(f"LỖI khi xử lý ID={order_id}: {e}", exc_info=True)
                continue  # Rất quan trọng: đảm bảo vòng lặp tiếp tục
        
        logging.info(f"Hoàn tất quá trình quét. Đã xử lý thành công {processed_count}/{total_orders} đơn hàng.")

    finally:
        # Khối finally đảm bảo rằng trình duyệt sẽ luôn được đóng,
        # ngay cả khi có lỗi không mong muốn xảy ra trong khối try.
        if driver is not None:
            logging.info("Đóng trình duyệt Selenium...")
            driver.quit()
