import calendar
import logging
import os
import time

import pandas as pd
import requests
from requests.adapters import HTTPAdapter
from requests.packages import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

API_URL = "https://pacs.osha.gov.tw/api/v1/getdangerocupation"
DEFAULT_OUTPUT_DIR = r"D:\營造業職災風險自動化評估系統\1_數據工程與法律合規層"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)


def get_current_month_range():
    year = int(time.strftime("%Y"))
    month = int(time.strftime("%m"))
    _, last_day = calendar.monthrange(year, month)
    start_date = f"{year}{month:02d}01"
    end_date = f"{year}{month:02d}{last_day:02d}"
    month_str = time.strftime("%Y%m")
    return start_date, end_date, month_str


def fetch_and_filter_osha_data(output_dir: str = DEFAULT_OUTPUT_DIR):
    start_date, end_date, month_str = get_current_month_range()
    os.makedirs(output_dir, exist_ok=True)

    output_filename = f"01_營造業105_115年歷史職災數據庫_{month_str}.csv"
    output_path = os.path.join(output_dir, output_filename)

    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json, text/plain, */*",
        "Connection": "close",
    }

    params = {
        "info_PostdateS": start_date,
        "info_PostdateE": end_date,
    }

    session = requests.Session()
    session.mount("https://", HTTPAdapter(max_retries=3))

    try:
        response = session.get(
            API_URL,
            headers=headers,
            params=params,
            verify=False,
            timeout=20,
        )
        response.raise_for_status()

        data = response.json()
        if isinstance(data, dict) and "data" in data:
            data = data["data"]

        total_rows = len(data)

        cleaned_records = []
        for item in data:
            industry = item.get("行業別", item.get("行業名稱", ""))
            if "營造業" not in str(industry):
                continue

            cleaned_records.append({
                "發生日期時間": item.get("發生日期", "無資料"),
                "公司名稱": item.get("事業單位", item.get("單位名稱", "無資料")),
                "工程名稱": item.get("工程名稱", "無資料"),
                "事故詳細地址": item.get("地址", "無資料"),
                "災害類型": item.get("災害類型", "無資料"),
                "罹災人數": item.get("罹災人數（數量）", item.get("罹災人數", "無資料")),
                "場所肇災處(事故經過)": item.get("場所（肇災處）", item.get("事故經過", "無資料")),
            })

        df = pd.DataFrame(cleaned_records)
        filtered_rows = len(df)

        if filtered_rows > 0:
            df.to_csv(output_path, index=False, encoding="utf-8-sig")
            status = f"本月共有 {total_rows} 筆職災資料，其中營造業 {filtered_rows} 筆。"
        else:
            summary_df = pd.DataFrame([{
                "月份": month_str,
                "查詢起日": start_date,
                "查詢迄日": end_date,
                "本月原始總筆數": total_rows,
                "營造業筆數": 0,
                "狀態": "本月共有職災資料，但未篩選到營造業案件。"
            }])
            summary_df.to_csv(output_path, index=False, encoding="utf-8-sig")
            status = f"本月共有 {total_rows} 筆職災資料，但沒有營造業資料。"

        logging.info(status)
        return {
            "month": month_str,
            "total_rows": total_rows,
            "filtered_rows": filtered_rows,
            "output_path": output_path,
            "status": status,
        }

    except Exception as e:
        summary_df = pd.DataFrame([{
            "月份": month_str,
            "查詢起日": start_date,
            "查詢迄日": end_date,
            "本月原始總筆數": "",
            "營造業筆數": "",
            "狀態": f"查詢失敗：{e}"
        }])
        summary_df.to_csv(output_path, index=False, encoding="utf-8-sig")

        logging.exception("查詢失敗，仍已建立摘要檔。")
        return {
            "month": month_str,
            "total_rows": None,
            "filtered_rows": None,
            "output_path": output_path,
            "status": f"查詢失敗：{e}",
        }


def main():
    result = fetch_and_filter_osha_data()
    print(result["status"])
    print(f"檔案位置：{result['output_path']}")


if __name__ == "__main__":
    main()