import time
import logging

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from .caspio_api import SLOT_MAP

def open_and_fill(driver: webdriver.Chrome,
                  link: str,
                  khung_gio: str,
                  order: dict,
                  order_id: str) -> bool:
    """
    Mở link tracking, chọn khung giờ giao, điền form với logging chi tiết.
    """
    wait = WebDriverWait(driver, 15)
    
    log_prefix = f"[Selenium][ID={order_id}]"

    logging.info(f"{log_prefix} Bắt đầu quy trình open_and_fill.")
    
    logging.info(f"{log_prefix} 1. Đang mở link: {link}")
    driver.get(link)
    time.sleep(2)

    logging.info(f"{log_prefix} 2. Click vào nút '配達変更のお申し込み' (Yêu cầu thay đổi lịch giao).")
    wait.until(EC.element_to_be_clickable(
        (By.XPATH, "//img[@alt='配達変更のお申し込み']/ancestor::a[1]"))
    ).click()
    time.sleep(2)
    
    logging.info(f"{log_prefix} 3. Chuyển sang cửa sổ mới.")
    driver.switch_to.window(driver.window_handles[-1])

    logging.info(f"{log_prefix} 4. Chọn 'ご自宅等' (Tại nhà của quý khách).")
    wait.until(EC.element_to_be_clickable(
        (By.XPATH, "//input[@type='radio' and @value='1']"))
    ).click()

    logging.info(f"{log_prefix} 5. Click nút '次へ進む' (Tiếp tục).")
    wait.until(EC.element_to_be_clickable(
        (By.XPATH, "//input[@name='receriptSubmit']"))
    ).click()
    time.sleep(2)

    logging.info(f"{log_prefix} 6. Tìm và chọn khung giờ.")
    desired = SLOT_MAP.get(khung_gio)
    first_selected = False
    if desired:
        logging.info(f"{log_prefix}    - Khung giờ yêu cầu: '{khung_gio}' -> Map sang giá trị: '{desired}'")
        js = f"""
        return (function() {{
          const title = "{desired}";
          const rows = Array.from(document.querySelectorAll(
              'table.tableType01 tbody > tr'));
          for (let i = 0; i < rows.length; i++) {{
            const r = rows[i].querySelector(
                'input[type="radio"][title="' + title + '"]');
            if (r && !r.disabled) {{
              console.log('Found radio button at row ' + i);
              r.click();
              return i === 0;
            }}
          }}
          console.log('Radio button for title "' + title + '" not found or disabled.');
          return null;
        }})();
        """
        result = driver.execute_script(js)
        if result is None:
            logging.error(f"{log_prefix}    - LỖI: Không tìm thấy hoặc không thể chọn khung giờ '{desired}' trên trang web.")
            raise RuntimeError(f"Không thể chọn khung giờ '{desired}' cho ID={order_id}")
        first_selected = result
        logging.info(f"{log_prefix}    - Đã chọn thành công. Khung giờ nằm ở ngày đầu tiên: {first_selected}")
        time.sleep(1)
    else:
        logging.error(f"{log_prefix}    - LỖI: Không tìm thấy giá trị mapping cho khung giờ '{khung_gio}' trong SLOT_MAP.")
        raise ValueError(f"Khung giờ '{khung_gio}' không hợp lệ cho ID={order_id}")

    logging.info(f"{log_prefix} 7. Điền thông tin vào form.")
    ma_buu_dien = order.get('ma_buu_dien', '').replace('-', '')
    email = order.get('Email_Tao', '')
    logging.info(f"{log_prefix}    - Mã bưu điện: {ma_buu_dien}")
    logging.info(f"{log_prefix}    - Email: {email}")

    driver.find_element(By.ID, 'clientPostCode').send_keys(ma_buu_dien)
    driver.find_element(By.NAME, 'clientTelNoArea').send_keys('080')
    driver.find_element(By.NAME, 'clientTelNoCityExchange').send_keys('745')
    driver.find_element(By.NAME, 'clientTelNoMember').send_keys('6068')
    driver.find_element(By.NAME, 'clientName').send_keys("ホアン　チォン　フン")
    driver.find_element(By.NAME, 'emailAddr').send_keys(email)
    driver.find_element(By.NAME, 'emailAddrConfirm').send_keys(email)
    logging.info(f"{log_prefix}    - Đã điền xong.")

    logging.info(f"{log_prefix} 8. Click nút '次へ進む' (Tiếp tục) để xác nhận.")
    wait.until(EC.element_to_be_clickable(
        (By.XPATH, "//input[@name='submit' and @value='次へ進む']"))
    ).click()
    time.sleep(2)

    logging.info(f"{log_prefix} 9. Click nút '登録する' (Đăng ký) để hoàn tất.")
    wait.until(EC.element_to_be_clickable(
        (By.XPATH, "//input[@name='submit' and @value='登録する']"))
    ).click()
    time.sleep(2)

    logging.info(f"{log_prefix} Quy trình open_and_fill hoàn tất.")
    return first_selected
