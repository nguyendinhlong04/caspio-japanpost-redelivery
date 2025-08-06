"""
Điểm vào chính: lấy token, truy vấn đơn & xử lý.
"""
from .caspio_api import get_access_token, fetch_orders
from .processor import process_orders


def main() -> None:
    print("Lấy token Caspio…")
    token = get_access_token()

    print("Lấy đơn Vắng nhà…")
    orders = fetch_orders(token)
    print(f"Tìm thấy {len(orders)} đơn Vắng nhà")

    process_orders(orders, token)
    print("HOÀN THÀNH")


if __name__ == "__main__":
    main()
