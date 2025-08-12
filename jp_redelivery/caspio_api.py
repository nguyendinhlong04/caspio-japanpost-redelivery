"""
Hàm truy cập Caspio REST: lấy token, truy vấn đơn 'Vắng nhà',
và cập nhật trạng thái sau khi đặt lại lịch giao.
"""
from __future__ import annotations

import json
import urllib.parse
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any

import requests

from .config import CASPIO_BASE_URL, CASPIO_CLIENT_ID, CASPIO_CLIENT_SECRET, CASPIO_TABLE_NAME

# Ánh xạ khung giờ dùng khi click trên Japan Post
SLOT_MAP: Dict[str, str] = {
    "午前中(8～12時)": "午前中(8～12時)",
    "１２－１４時": "12～14時",
    "１４－１６時": "14～16時",
    "１６－１８時": "16～18時",
    "１８－２０時": "18～20時",
    "１９－２１時": "19～21時"
}


def get_access_token() -> str:
    url = f"{CASPIO_BASE_URL}/oauth/token"
    payload = {
        "grant_type": "client_credentials",
        "client_id": CASPIO_CLIENT_ID,
        "client_secret": CASPIO_CLIENT_SECRET,
    }
    res = requests.post(url, data=payload,
                        headers={"Content-Type": "application/x-www-form-urlencoded"})
    res.raise_for_status()
    return res.json()["access_token"]



def fetch_orders(token: str) -> List[Dict[str, Any]]:
    where_clause = "tinh_trang_van_chuyen='Vắng nhà'"
    
    encoded_where = urllib.parse.quote(where_clause)
    
    url = f"{CASPIO_BASE_URL}/rest/v2/tables/{CASPIO_TABLE_NAME}/records?where={encoded_where}"
    
    print(f"DEBUG: Requesting URL: {url}")
    
    res = requests.get(url, headers={"Authorization": f"Bearer {token}"})
    res.raise_for_status()
    
    print(f"DEBUG: API Response: {res.text}") 
    
    return res.json().get("Result", [])

def update_order(token: str, id_value: str | int, first_selected: bool) -> None:
    tz = timezone(timedelta(hours=9))
    today = datetime.now(tz).date()
    target = today if first_selected else today + timedelta(days=1)
    patch_date = target.strftime("%m/%d/%Y")

    where_clause = f"ID={id_value}" if str(id_value).isdigit() else f"ID='{id_value}'"
    url = f"{CASPIO_BASE_URL}/rest/v2/tables/{CASPIO_TABLE_NAME}/records"
    data = {
        "tinh_trang_van_chuyen": "Đã hẹn giao lại",
        "ngayhenlai": patch_date
    }
    res = requests.put(
        url,
        params={"q.where": where_clause},
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        },
        json=data
    )
    res.raise_for_status()
    print(f"   → Updated ID={id_value} → ngayhenlai={patch_date}")
