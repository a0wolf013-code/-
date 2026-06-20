#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
專案名稱：營造業職災風險自動化評估系統
模組名稱：2_演算法與大腦訓練層 / 11_基地地質參數讀取.py
功能描述：結構化工程地質參數讀取器。全自動搜尋並讀取施工計畫書中的
          地下水位（GL-m）與臨界安全係數（FS），執行標準化特徵提取，
          為下游 12 號物理與法律風險計算引擎提供客觀之地質物理邊界特徵。
"""

import os
import sys
import glob
import pandas as pd
import numpy as np

# 確保支援繁體中文路徑與輸出
sys.stdout.reconfigure(encoding='utf-8') if hasattr(sys.stdout, 'reconfigure') else None

def 智慧提取地質參數(df):
    """
    模糊欄位關鍵字掃描器：
    自動適應不同工程計畫書的欄位黑話，精準提取地下水位與安全係數。
    """
    # 預設專家保底規範值 (符合營造與大地構造設計規範標準)
    地下水位 = -5.0
    安全係數 = 1.5
    
    # A. 智慧搜尋「地下水位」欄位
    水位關鍵字 = ["地下水位", "水位", "gl-m", "gl", "water level", "water_level"]
    水位欄位 = None
    for col in df.columns:
        if any(kw in str(col).lower() for kw in 水位關鍵字):
            水位欄位 = col
            break
            
    if 水位欄位:
        # 取第一筆有效數值，並確保轉為浮點數
        數值 = pd.to_numeric(df[水位欄位], errors='coerce').dropna()
        if not 數值.empty:
            地下水位 = float(數值.iloc[0])
            # 自動防禦：台灣習慣水位用負數表示(如 GL-5m)，若使用者打成正數，自動校正為負數
            if 地下水位 > 0:
                地下水位 = -地下水位
            print(f"   💧 [成功捕獲] 地下水位 (GL-m)：{地下水位} 公尺 (欄位名稱: {水位欄位})")
    else:
        print(f"   ⚠️ [提示] 計畫書中未發現地下水位欄位，自動啟用專家規範值：{地下水位} 公尺")

    # B. 智慧搜尋「臨界安全係數」欄位
    係數關鍵字 = ["安全係數", "臨界安全係數", "臨界係數", "fs", "safety_factor", "factor of safety"]
    係數欄位 = None
    for col in df.columns:
        if any(kw in str(col).lower() for kw in 係數關鍵字):
            係數欄位 = col
            break
            
    if 係數欄位:
        數值 = pd.to_numeric(df[係數欄位], errors='coerce').dropna()
        if not 數值.empty:
            安全係數 = float(數值.iloc[0])
            print(f"   🛡️ [成功捕獲] 臨界安全係數 (FS)：{安全係數} (欄位名稱: {係數欄位})")
    else:
        print(f"   ⚠️ [提示] 計畫書中未發現安全係數欄位，自動啟用專家規範值：{安全係數}")

    return 地下水位, 安全係數

def main():
    # =========================================================================
    # 1. 路徑定義與多格式智慧檔案掃描
    # =========================================================================
    第二層路徑 = "D:/營造業職災風險自動化評估系統/2_演算法與大腦訓練層"
    輸出路徑 = os.path.join(第二層路徑, "11_結構化基地地質特徵矩陣.csv")
    
    print("==================================================")
    print("🚀 正在啟動 [11_結構化基地地質參數讀取系統] ...")
    print("==================================================")
    
    # 智慧型檔案掃描：優先搜尋 Excel，若無則搜尋 CSV 檔案
    計畫書_xlsx = glob.glob(os.path.join(第二層路徑, "*計畫書*.xlsx"))
    計畫書_csv = glob.glob(os.path.join(第二層路徑, "*計畫書*.csv"))
    地質檔_xlsx = glob.glob(os.path.join(第二層路徑, "*地質*.xlsx"))
    地質檔_csv = glob.glob(os.path.join(第二層路徑, "*地質*.csv"))
    
    # 整合所有可能的名字
    候選檔案 = 計畫書_xlsx + 計畫書_csv + 地質檔_xlsx + 地質檔_csv
    
    # =========================================================================
    # 2. 執行安全雙軌載入策略
    # =========================================================================
    df_plan = None
    if 候選檔案:
        實際檔案 = 候選檔案[0]
        檔名 = os.path.basename(實際檔案)
        print(f"📂 [智慧偵測] 成功尋找到最接近的基地地質計畫書：{檔名}")
        try:
            if 實際檔案.lower().endswith(('.xlsx', '.xls')):
                df_plan = pd.read_excel(實際檔案)
            else:
                df_plan = pd.read_csv(實際檔案, encoding='utf-8-sig', on_bad_lines='skip')
        except Exception as e:
            print(f"   ⚠️ 讀取實體檔案失敗，原因: {e}。系統將自動切換為全模組防禦保底機制...")
    else:
        print("⚠️ [無實體計畫書] 資料夾中目前沒有放置含有『計畫書』或『地質』字眼的 Excel/CSV 檔案。")
        print("💡 系統已自動啟動【無縫防禦機制】，將直接產出通用標準專家矩陣，保證全系統不中斷！")

    # =========================================================================
    # 3. 特徵提取與結構化導出
    # =========================================================================
    print("\n⏳ 正在分析計畫書表格，淬鍊硬核大地工程物理參數...")
    
    # 呼叫參數提取核心
    if df_plan is not None and not df_plan.empty:
        水位值, 係數值 = 智慧提取地質參數(df_plan)
    else:
        # 完全無檔案時的專家標準規範值
        水位值, 係數值 = -5.0, 1.5
        
    # 打包成結構化的特徵矩陣
    地質特徵 = {
        "基地物理特徵_地下水位(GL-m)": [水位值],
        "基地物理特徵_臨界安全係數(FS)": [係數值]
    }
    df_geology = pd.DataFrame(地質特徵)
    
    # 匯出結構化 CSV
    try:
        df_geology.to_csv(輸出路徑, index=False, encoding="utf-8-sig")
        print("==================================================")
        print(f"🎉 [成功] 11 號基地地質參數結構化讀取工程圓滿完成！")
        print(f"📊 淬鍊物理參數：地下水位={水位值}m, 安全係數(FS)={係數值}")
        print(f"📂 結構化特徵矩陣儲存路徑：{輸出路徑}")
        print("==================================================")
    except Exception as e:
        print(f"❌ 匯出地質特徵矩陣失敗，原因: {e}")

if __name__ == "__main__":
    main()
