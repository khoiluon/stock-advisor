# backend/test_ssi_connection.py

import os
import requests
import json
from dotenv import load_dotenv

# --- 1. TẢI CÁC BIẾN MÔI TRƯỜNG TỪ FILE .env ---
load_dotenv()
print("Đã tải các biến môi trường...")

# --- 2. CẤU HÌNH ---
SSI_API_BASE_URL = "https://fc-data.ssi.com.vn/api/v2/"

CONSUMER_ID = os.getenv('SSI_FCDATA_CONSUMER_ID')
CONSUMER_SECRET = os.getenv('SSI_FCDATA_CONSUMER_SECRET')

if not all([CONSUMER_ID, CONSUMER_SECRET]):
    print("\n!!! LỖI: Không tìm thấy SSI_FCDATA_CONSUMER_ID hoặc SSI_FCDATA_CONSUMER_SECRET trong file .env")
    exit()

print(f"Sử dụng Consumer ID: {CONSUMER_ID[:4]}...{CONSUMER_ID[-4:]}")


def get_access_token():
    """
    Gửi yêu cầu lấy Access Token từ SSI
    """
    token_url = f"{SSI_API_BASE_URL}Market/AccessToken"

    headers = {
        "Content-Type": "application/json"
    }

    payload = {
        "consumerID": CONSUMER_ID,
        "consumerSecret": CONSUMER_SECRET
    }

    print(f"\n--- Đang gửi yêu cầu lấy Access Token đến: {token_url} ---")

    try:
        response = requests.post(token_url, headers=headers, json=payload)

        if response.status_code == 200:
            data = response.json()
            if data.get("status") == 200:
                access_token = data["data"]["accessToken"]
                print("✅ LẤY TOKEN THÀNH CÔNG!")
                return access_token
            else:
                print(f"❌ LỖI: {data}")
                return None
        else:
            print(f"❌ LỖI HTTP {response.status_code}: {response.text}")
            return None

    except requests.exceptions.RequestException as e:
        print(f"❌ LỖI KẾT NỐI: {e}")
        return None


def get_securities(access_token, market="HOSE", page=1, page_size=5):
    """
    Lấy danh sách mã chứng khoán
    """
    url = f"{SSI_API_BASE_URL}Market/Securities?pageIndex={page}&pageSize={page_size}&market={market}"

    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    print(f"\n--- Đang gửi yêu cầu lấy danh sách cổ phiếu từ: {url} ---")

    try:
        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            data = response.json()
            print("✅ LẤY DANH SÁCH CỔ PHIẾU THÀNH CÔNG!")
            print(json.dumps(data, indent=2, ensure_ascii=False))
        else:
            print(f"❌ LỖI HTTP {response.status_code}: {response.text}")

    except requests.exceptions.RequestException as e:
        print(f"❌ LỖI KẾT NỐI: {e}")


# --- HÀM CHÍNH ---
if __name__ == "__main__":
    token = get_access_token()
    if token:
        get_securities(token, market="HOSE", page=1, page_size=10)
