import pandas as pd
import os
import re

def 執行裁罰紀錄數據對齊():
    print("==========================================")
    print("🚀 啟動【第一波：築基期】數據結構化清理模組...")
    print("==========================================")

    資料夾路徑 = r"D:\營造業職災風險自動化評估系統\1_數據工程與法律合規層"
    原始檔名 = "03_02歷史法令裁罰原始母表.csv"
    輸入路徑 = os.path.join(資料夾路徑, 原始檔名)
    輸出路徑 = os.path.join(資料夾路徑, "歷史法令裁罰原始母表.csv")

    if not os.path.exists(輸入路徑):
        print(f"❌ 找不到檔案：{輸入路徑}")
        return

    # --- 核心邏輯：自動尋找正確的標題列 ---
    print(f"🔍 正在偵測 {原始檔名} 的結構...")
    
    found_header = False
    for i in range(5):  # 嘗試跳過 0 到 4 行來尋找標題
        try:
            temp_df = pd.read_csv(輸入路徑, encoding='utf-8-sig', skiprows=i, nrows=0)
            if any("事業單位名稱" in str(col) for col in temp_df.columns):
                print(f"🎯 成功！在第 {i+1} 行找到正確標題列。")
                df = pd.read_csv(輸入路徑, encoding='utf-8-sig', skiprows=i)
                found_header = True
                break
        except:
            continue

    if not found_header:
        print("⚠️  UTF-8 偵測失敗，嘗試 Big5 編碼...")
        for i in range(5):
            try:
                temp_df = pd.read_csv(輸入路徑, encoding='big5', skiprows=i, nrows=0)
                if any("事業單位名稱" in str(col) for col in temp_df.columns):
                    print(f"🎯 成功！在第 {i+1} 行找到標題 (Big5)。")
                    df = pd.read_csv(輸入路徑, encoding='big5', skiprows=i)
                    found_header = True
                    break
            except:
                continue

    if not found_header:
        print("❌ 致命錯誤：掃描前 5 行後仍找不到包含『事業單位名稱』的標題。")
        return

    # --- 欄位正規化 ---
    df.columns = [str(c).replace('\n', '').replace('\r', '').strip() for c in df.columns]
    
    # 對齊職安法第 49 條要求之欄位 [3]
    mapping = {}
    for c in df.columns:
        if "事業單位名稱" in c: mapping[c] = "事業單位名稱"
        if "處分日期" in c: mapping[c] = "處分日期"
        if "違反法規條款" in c: mapping[c] = "違反條文"
        if "罰鍰金額" in c: mapping[c] = "罰鍰金額"
    
    df = df.rename(columns=mapping)

    # 為了檔案 04 的 FuzzyWuzzy 匹配清理名稱 [4]
    df["事業單位名稱"] = df["事業單位名稱"].apply(lambda x: re.sub(r'\(.*\)', '', str(x)).strip())

    # 輸出最終標準母表 [1]
    df.to_csv(輸出路徑, index=False, encoding='utf-8-sig')
    print(f"✅ 清理完成！共計 {len(df)} 筆有效紀錄。")
    print(f"📂 儲存至：{輸出路徑}")

if __name__ == "__main__":
    執行裁罰紀錄數據對齊()