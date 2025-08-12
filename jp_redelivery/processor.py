from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from selenium import webdriver

from .caspio_api import update_order
from .japanpost import open_and_fill  

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def process_orders(all_orders: list[dict], token: str) -> None:
    
    orders_to_process = []
    target_status = "Vắng nhà"
    
    logging.info("================== BẮT ĐẦU LỌC CLIENT-SIDE ==================")
    logging.info(f"Tổng số đơn hàng lấy về từ Caspio: {len(all_orders)}")
    logging.info(f"Đang tìm các đơn có 'tinh_trang_van_chuyen' == '{target_status}'")

    for order in all_orders:
        order_id = order.get('ID', 'N/A')
        status = order.get('tinh_trang_van_chuyen')
        
        logging.info(f"  - Checking ID: {order_id}, Status: '{status}'")
        logging.info(f"    Raw repr(): {repr(status)}")

        if status and status.strip() == target_status:
            logging.info(f"    [MATCH!] ID: {order_id} được đưa vào danh sách xử lý.")
            orders_to_process.append(order)

    logging.info(f"KẾT THÚC LỌC. Tìm thấy {len(orders_to_process)} đơn hàng phù hợp.")
    logging.info("=====================================================================")

    if not orders_to_process:
        logging.warning("Không có đơn hàng nào thỏa mãn điều kiện để xử lý. Dừng chương trình.")
        return
        
    driver: webdriver.Chrome | None = None
    tz = timezone(timedelta(hours=9))
    today = datetime.now(tz).date()

    try:
        total_orders = len(orders_to_process)
        processed_count = 0

        for index, order in enumerate(orders_to_process):
            order_id = order.get('ID', 'N/A')
            logging.info(f"BẮT ĐẦU XỬ LÝ ĐƠN HÀNG {index + 1}/{total_orders} (ID: {order_id})")
            
            try:
                if order.get('don_vi_van_chuyen') != "JapanPost":
                    logging.warning(f"   → Bỏ qua ID={order_id} vì 'don_vi_van_chuyen' là '{order.get('don_vi_van_chuyen')}'")
                    continue

                reschedule_date_str = order.get('ngayhenlai')
                if reschedule_date_str and str(reschedule_date_str).lower() != "nan":
                    try:
                        reschedule_date = datetime.fromisoformat(reschedule_date_str.split("T")[0]).date()
                        if reschedule_date >= today:
                            logging.info(f"   → Bỏ qua ID={order_id} vì đã hẹn lại vào {reschedule_date}")
                            continue
                    except (ValueError, TypeError):
                        logging.warning(f"   → Không thể phân tích 'ngayhenlai' cho ID={order_id}. Giá trị: '{reschedule_date_str}'. Vẫn tiếp tục xử lý.")

                
                link = order.get('LinkVanChuyen')
                khung_gio = order.get('khung_gio_giao')
                if not all([link, khung_gio]):
                    logging.warning(f"   → Bỏ qua ID={order_id} vì thiếu Link hoặc Khung giờ")
                    continue

                if driver is None:
                    logging.info("Khởi tạo trình duyệt Selenium...")
                    opts = webdriver.ChromeOptions()
                    opts.add_argument("--headless=new")
                    opts.add_argument("--no-sandbox")
                    opts.add_argument("--disable-dev-shm-usage")
                    driver = webdriver.Chrome(options=opts)

                logging.info(f">> Bắt đầu xử lý Selenium cho ID={order_id}")
                first_day_selected = open_and_fill(driver, link, khung_gio, order, order_id)
                update_order(token, order_id, first_day_selected)

                processed_count += 1
                logging.info(f"KẾT THÚC XỬ LÝ ID={order_id} THÀNH CÔNG")

            except Exception as e:
                logging.error(f"LỖI khi xử lý ID={order_id}: {e}", exc_info=True)
                continue

        logging.info(f"Hoàn tất. Đã xử lý thành công {processed_count}/{total_orders} đơn hàng.")

    finally:
        if driver is not None:
            logging.info("Đóng trình duyệt Selenium.")
            driver.quit()
