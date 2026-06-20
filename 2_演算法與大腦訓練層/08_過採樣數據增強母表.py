#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
專案名稱：營造業職災風險自動化評估系統
模組名稱：2_演算法與大腦訓練層 / 08_數據過採樣.py
功能描述：利用 SMOTE 演算法對極度不平衡的 SOI Level 1~5 職災樣本進行過採樣，
          [內建自修復功能] 啟動時自動檢測與對齊 Python 3.13 最新環境相容套件，
          徹底解決機器學習模型的偏見問題，生成平衡的數據增強矩陣。
"""

import os
import sys
import subprocess

# =========================================================================
# 0. 智慧型環境自修復核心 (防禦 Python 3.13 世紀大打架與 ModuleNotFoundError)
# =========================================================================
try:
    from imblearn.over_sampling import SMOTE
    import sklearn
except (ModuleNotFoundError, ImportError):
    print("⏳ [環境異常/遺失] 系統正在自動修復、對齊並強充套件環境，大約需要 15 秒...")
    try:
        # 強制利用目前運行的執行緒，背景全自動拉取與 Python 3.13 完美互通的最新相容包
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "scikit-learn", "imbalanced-learn"])
        print("🎉 [成功] 環境自修復完成！正在引導核心重新讀取...")
        from imblearn.over_sampling import SMOTE
    except Exception as final_e:
        print(f"❌ 終極修復失敗，請嘗試手動重啟 Spyder 軟體。錯誤原因: {final_e}")
        sys.exit(1)

import pandas as pd
import numpy as np

# 確保支援繁體中文路徑與輸出
sys.stdout.reconfigure(encoding='utf-8') if hasattr(sys.stdout, 'reconfigure') else None

def main():
    # =========================================================================
    # 1. 路徑定義與 07 號集群母表載入
    # =========================================================================
    第二層路徑 = "D:/營造業職災風險自動化評估系統/2_演算法與大腦訓練層"
    輸入路徑 = os.path.join(第二層路徑, "07_嚴重度集群分析母表.csv")
    輸出路徑 = os.path.join(第二層路徑, "08_過採樣數據增強母表.csv")
    
    print("==================================================")
    print("🚀 正在啟動 [08_數據過採樣與增強系統 (SMOTE)] ...")
    print("==================================================")
    
    if not os.path.exists(輸入路徑):
        print(f"❌ 找不到嚴重度集群母表！請先確認 07 號腳本是否已執行成功：\n   {輸入路徑}")
        return
        
    try:
        df = pd.read_csv(輸入路徑, encoding="utf-8-sig")
        print(f"📊 成功載入集群母表，原始規模為：{df.shape} (筆數, 欄位數)")
    except Exception as e:
        print(f"❌ 讀取集群母表失敗，原因: {e}")
        return

    # =========================================================================
    # 2. X/y 分離與機器學習數值特徵工程 (編碼轉換)
    # =========================================================================
    print("⏳ 正在抽取 AI 特徵矩陣並對文字欄位進行數值化編碼...")
    
    目標欄位 = "風險嚴重度_SOI_Level"
    if 目標欄位 not in df.columns:
        print(f"❌ 錯誤：資料表中缺乏 07 號產出的 {目標欄位} 欄位！")
        return
        
    特徵欄位 = [col for col in df.columns if col.startswith("特徵_") or col.startswith("缺失_") or col == "工種_"]
    
    X_raw = df[特徵欄位].copy()
    if "特徵_工種別" in X_raw.columns:
        # 強制將新版 get_dummies 產出的 True/False 轉為 1/0，完美防禦新版 SMOTE
        X_raw = pd.get_dummies(X_raw, columns=["特徵_工種別"], drop_first=False, dtype=int)
        
    # 確保特徵中完全沒有非數值資料
    X_numeric = X_raw.select_dtypes(include=[np.number, bool]).fillna(0).astype(float)
    y = df[目標欄位]
    
    print(f"   [特徵就位] 參與過採樣的高維度特徵共有：{X_numeric.shape} 個維度。")
    print(f"   📊 原始風險等級分佈：\n{y.value_counts().sort_index()}")

    # =========================================================================
    # 3. 智慧型 SMOTE 參數優化與動態鄰居防禦機制
    # =========================================================================
    print("\n⏳ 核心過採樣演算法啟動，正在模擬生成少數重大職災樣本...")
    
    最小樣本數 = y.value_counts().min()
    
    if 最小樣本數 < 2:
        print("💡 [提示] 檢測到極罕見職災群集(僅1筆個案)，自動啟用鄰居限制保底機制...")
        孤立標籤 = y.value_counts()[y.value_counts() == 1].index
        for label in 孤立標籤:
            孤立樣本_X = X_numeric[y == label]
            孤立樣本_y = y[y == label]
            X_numeric = pd.concat([X_numeric, 孤立樣本_X, 孤立樣本_X], axis=0, ignore_index=True)
            y = pd.concat([y, 孤立樣本_y, 孤立樣本_y], axis=0, ignore_index=True)
        鄰居設定 = 1
    else:
        鄰居設定 = min(5, 最小樣本數 - 1)
        
    print(f"   ⚙️ 演算法動態配置：k_neighbors 調整為：{鄰居設定}")

    # 執行 SMOTE
    smote = SMOTE(k_neighbors=鄰居設定, random_state=42)
    X_resampled, y_resampled = smote.fit_resample(X_numeric, y)

    # =========================================================================
    # 4. 特徵還原與結構化融合重組
    # =========================================================================
    df_balanced = pd.DataFrame(X_resampled, columns=X_numeric.columns)
    df_balanced[目標欄位] = y_resampled
    
    布林欄位 = [col for col in df_balanced.columns if col.startswith("缺失_") or col.startswith("工種_")]
    df_balanced[布林欄位] = df_balanced[布林欄位].round().astype(int)

    # =========================================================================
    # 5. 匯出「AI 平衡黃金母體特徵矩陣」
    # =========================================================================
    try:
        df_balanced.to_csv(輸出路徑, index=False, encoding="utf-8-sig")
        print("\n==================================================")
        print(f"🎉 [成功] 08 號數據過採樣與增強工程完工！")
        print(f"📊 平衡後大數據規模：{df_balanced.shape} (預測燃料已完全拉平)")
        print(f"🕵️‍♂️ SMOTE 數據增強後風險等級分佈：")
        
        新分佈 = df_balanced[目標欄位].value_counts().sort_index()
        for lvl, count in 新分佈.items():
            print(f"   📈 {lvl} ：已平衡擴充至 {count} 筆虛擬/實體特徵樣本")
            
        print(f"📂 AI 訓練用平衡母表儲存路徑：{輸出路徑}")
        print("==================================================")
    except Exception as e:
        print(f"❌ 匯出平衡矩陣失敗，原因: {e}")

if __name__ == "__main__":
    main()
