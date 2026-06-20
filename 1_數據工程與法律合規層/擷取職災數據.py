import os
import pandas as pd
import requests
from requests.adapters import HTTPAdapter
from requests.packages import urllib3

# 關閉 SSL 安全警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def fetch_and_filter_osha_data():
    # 強制使用 pacs 直連網址，避免導向到主網域 osha.gov.tw 導致 DNS 錯誤
    api_url = "https://pacs.osha.gov.tw/api/v1/getdangerocupation"
    print("正在從職安署 API 請求資料，請稍候...")

    # 完整瀏覽器標頭，防止被政府資安設備（WAF）直接阻斷 DNS 解析
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Connection": "close",  # 請求完立即關閉連線，防止 Max retries 錯誤
    }

    # 建立一個擁有重試機夾的 Session，應對不穩定的政府網路
    session = requests.Session()
    adapter = HTTPAdapter(max_retries=3)  # 自動重試 3 次
    session.mount("https://", adapter)

    try:
        # verify=False 繞過 SSL 憑證，timeout 設為 20 秒
        response = session.get(
            api_url, headers=headers, verify=False, timeout=20
        )

        if response.status_code != 200:
            print(f"❌ 連線失敗，伺服器回應代碼: {response.status_code}")
            return

        raw_data = response.json()
        print(f"✅ 成功下載資料！原始總筆數：{len(raw_data)} 筆")

        cleaned_records = []
        for item in raw_data:
            # 行業別過濾 (博士論文第三、五章範疇)
            industry = item.get("行業別", item.get("行業名稱", ""))
            if "營造業" not in str(industry):
                continue

            record = {
                "發生日期時間": item.get("發生日期", "無資料"),
                "公司名稱": item.get("事業單位", item.get("單位名稱", "無資料")),
                "工程名稱": item.get("工程名稱", "無資料"),
                "事故詳細地址": item.get("地址", "無資料"),
                "災害類型": item.get("災害類型", "無資料"),
                "罹災人數": item.get("罹災人數（數量）", item.get("罹災人數", "無資料")),
                "場所肇災處(事故經過)": item.get("場所（肇災處）", item.get("事故經過", "無資料")),
            }
            cleaned_records.append(record)

        df = pd.DataFrame(cleaned_records)
        print(f"📊 篩選完成！屬於營造業的職災個案共：{len(df)} 筆")

        if df.empty:
            print("⚠️ 警告：未篩選出營造業相關資料。")
            return

        output_filename = "osha_construction_disasters.csv"
        df.to_csv(output_filename, index=False, encoding="utf-8-sig")
        print(f"\n[成功] 結構化資料已儲存至：{os.path.abspath(output_filename)}")

    except requests.exceptions.ConnectionError as ce:
        print(
            f"❌ 網路連線/DNS 解析失敗。\n原因提示：你的網路環境目前無法解析 pacs.osha.gov.tw。\n詳細錯誤：{ce}"
        )
    except Exception as e:
        print(f"❌ 其他錯誤: {e}")


if __name__ == "__main__":
    fetch_and_filter_osha_data()
