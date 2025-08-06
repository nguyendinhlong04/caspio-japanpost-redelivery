"""
Tương tác Selenium với trang Japan Post để đặt lại lịch giao.
Giữ nguyên logic của script gốc.
"""
import time

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from .caspio_api import SLOT_MAP


def open_and_fill(driver: webdriver.Chrome,
                  link: str,
                  khung_gio: str,
                  order: dict) -> bool:
    """
    Mở link tracking, chọn khung giờ giao, điền form.
    Trả về True nếu khung giờ được chọn nằm ở hàng đầu tiên (dùng để
    quyết định hẹn giao hôm nay hay ngày mai).
    """
    wait = WebDriverWait(driver, 15)
    driver.get(link)
    time.sleep(2)

    # 1) click “配達変更のお申し込み”
    wait.until(EC.element_to_be_clickable(
        (By.XPATH, "//img[@alt='配達変更のお申し込み']/ancestor::a[1]"))
    ).click()
    time.sleep(2)
    driver.switch_to.window(driver.window_handles[-1])

    # 2) chọn “ご自宅等”
    wait.until(EC.element_to_be_clickable(
        (By.XPATH, "//input[@type='radio' and @value='1']"))
    ).click()

    # 3) “次へ進む”
    wait.until(EC.element_to_be_clickable(
        (By.XPATH, "//input[@name='receriptSubmit']"))
    ).click()
    time.sleep(2)

    # 4) chọn khung giờ
    desired = SLOT_MAP.get(khung_gio)
    first_selected = False
    if desired:
        js = f"""
        return (function() {{
          const title = "{desired}";
          const rows = Array.from(document.querySelectorAll(
              'table.tableType01 tbody > tr'));
          for (let i = 0; i < rows.length; i++) {{
            const r = rows[i].querySelector(
                'input[type="radio"][title="' + title + '"]');
            if (r && !r.disabled) {{ r.click(); return i === 0; }}
          }}
          return false;
        }})();
        """
        first_selected = driver.execute_script(js)
        time.sleep(1)
    else:
        print(f"[WARN] Không tìm thấy SLOT_MAP cho {khung_gio}")

    # 5) điền form
    driver.find_element(By.ID, 'clientPostCode') \
          .send_keys(order.get('ma_buu_dien', '').replace('-', ''))
    driver.find_element(By.NAME, 'clientTelNoArea').send_keys('080')
    driver.find_element(By.NAME, 'clientTelNoCityExchange').send_keys('745')
    driver.find_element(By.NAME, 'clientTelNoMember').send_keys('6068')
    driver.find_element(By.NAME, 'clientName').send_keys("ホアン　チォン　フン")
    email = order.get('Email_Tao', '')
    driver.find_element(By.NAME, 'emailAddr').send_keys(email)
    driver.find_element(By.NAME, 'emailAddrConfirm').send_keys(email)

    # 6) “次へ進む”
    wait.until(EC.element_to_be_clickable(
        (By.XPATH, "//input[@name='submit' and @value='次へ進む']"))
    ).click()
    time.sleep(2)

    # 7) “登録する”
    wait.until(EC.element_to_be_clickable(
        (By.XPATH, "//input[@name='submit' and @value='登録する']"))
    ).click()
    time.sleep(2)

    return first_selected
