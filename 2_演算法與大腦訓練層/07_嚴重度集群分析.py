#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
專案名稱：營造業職災風險自動化評估系統
模組名稱：2_演算法與大腦訓練層 / 07_嚴重度集群分析.py
功能描述：利用 K-means 非監督式集群演算法，依據罹災人數與傷亡核心指標，
          自動將職災案件劃分為 5 個風險嚴重度等級 (SOI Level 1~5)，
          並將嚴重度標籤反向注入特徵母表中，為後續監督式預測模型提供黃金標籤 (Target Column)。
"""

import os
import sys
import pandas as pd
import numpy as np

# 引入 Scikit-Learn 機器學習核心套件
try:
    from sklearn.cluster import KMeans
    from sklearn.preprocessing import StandardScaler
except ModuleNotFoundError:
    print("❌ 偵測到遺失 scikit-learn 套件，請在系統終端機執行：pip install scikit-learn")
    sys.exit(1)

# 確保支援繁體中文路徑與輸出
sys.stdout.reconfigure(encoding='utf-8') if hasattr(sys.stdout, 'reconfigure') else None

def main():
    # =========================================================================
    # 1. 路徑定義與 05 號特徵母表載入
    # =========================================================================
    第二層路徑 = "D:/營造業職災風險自動化評估系統/2_演算法與大腦訓練層"
    輸入路徑 = os.path.join(第二層路徑, "05_特徵挖掘與自動標籤母表.csv")
    輸出路徑 = os.path.join(第二層路徑, "07_嚴重度集群分析母表.csv")
    
    print("==================================================")
    print("🚀 正在啟動 [07_嚴重度集群分析系統 (K-means)] ...")
    print("==================================================")
    
    if not os.path.exists(輸入路徑):
        print(f"❌ 找不到特徵標籤母表！請先確認 05 號腳本是否已執行成功：\n   {輸入路徑}")
        return
        
    try:
        df = pd.read_csv(輸入路徑, encoding="utf-8-sig")
        print(f"📊 成功載入 AI 特徵母表，共 {df.shape[0]} 筆職災個案。")
    except Exception as e:
        print(f"❌ 讀取特徵母表失敗，原因: {e}")
        return

    # =========================================================================
    # 2. 特徵提取與智慧型降級防禦工程 (特徵工程)
    # =========================================================================
    print("⏳ 正在提取死傷嚴重度核心指標並進行資料清洗...")
    
    # 智慧識別傷亡與停工指標欄位
    # 如果公開資料中缺乏「停工天數」，則動態以「罹災人數」與二進位缺失總和作為模擬風險強度指標
    指標欄位 = []
    
    # 優先檢查「罹災人數」或「死亡人數」
    for col in ["罹災人數", "死亡人數", "傷亡人數", "罹災死亡人數"]:
        if col in df.columns:
            指標欄位.append(col)
            break
            
    # 檢查是否含有「停工天數」
    for col in ["停工天數", "停工日", "復工天數"]:
        if col in df.columns:
            指標欄位.append(col)
            break
            
    # 降級防禦：若資料夾中的表格完全沒有這些數值欄位，則自動利用「缺失總數」來作為集群依據
    if not 指標欄位:
        print("💡 [提示] 未發現標準死傷與停工天數欄位，系統自動啟用特徵衍生防禦機制...")
        缺失欄位 = [col for col in df.columns if col.startswith("缺失_")]
        df["衍生_管理缺失總數"] = df[缺失欄位].sum(axis=1)
        指標欄位 = ["罹災人數", "衍生_管理缺失總數"] if "罹災人數" in df.columns else ["衍生_管理缺失總數"]
        
    print(f"   [特徵鎖定] 選用分群指標欄位：{指標欄位}")
    
    # 提取分群矩陣並處理空值
    X = df[指標欄位].copy()
    X = X.fillna(0) # 空值補 0 防禦

    # 核心步驟：特徵標準化 (Standardization)
    # K-means 依賴歐式距離，若「停工天數(如30天)」與「罹災人數(如1人)」不縮放到同一尺度，天數會霸凌人數。
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # =========================================================================
    # 3. 執行 K-means 集群演算法 (自動劃分 5 個嚴重度等級)
    # =========================================================================
    分群數 = 5
    print(f"\n⏳ 核心機器學習啟動：正在執行 K-means 演算法自動劃分 {分群數} 大群集...")
    
    # 內建 random_state 確保每次跑出來的群聚結果完全一致
    kmeans = KMeans(n_clusters=分群數, random_state=42, n_init=10)
    df["原始集群標籤"] = kmeans.fit_predict(X_scaled)

    # =========================================================================
    # 4. 智慧型標籤重組：依據嚴重度大小由小到大排序 (SOI Level 1 ~ 5)
    # =========================================================================
    print("⏳ 正在對分群結果進行科學排序，對齊 SOI Level 1~5 規範...")
    
    # 計算每個原始群集的「指標平均值」，用以評估哪一群才是真正的「極度嚴重」
    # 我們以指標欄的第一個（通常是罹災人數）作為主要排序權重
    主要指標 = 指標欄位[0]
    群集權重 = df.groupby("原始集群標籤")[主要指標].mean().sort_values()
    
    # 建立對照字典：平均死傷最少的是 Level 1，最多的是 Level 5
    標籤對照字典 = {}
    for level_idx, 原始標籤 in enumerate(群集權重.index):
        標籤對照字典[原始標籤] = f"SOI Level {level_idx + 1}"
        
    # 將客觀有序的黃金標籤寫入 DataFrame
    df["風險嚴重度_SOI_Level"] = df["原始集群標籤"].map(標籤對照字典)
    
    # 移除過渡用的原始標籤
    df = df.drop(columns=["原始集群標籤"])

    # =========================================================================
    # 5. 匯出嚴重度集群矩陣母表
    # =========================================================================
    try:
        df.to_csv(輸出路徑, index=False, encoding="utf-8-sig")
        print("\n==================================================")
        print(f"🎉 [成功] 07 號嚴重度集群分析工程完工！")
        print(f"📊 擴充母表規模：{df.shape} (包含全新 SOI 風險標籤欄位)")
        print(f"🕵️‍♂️ 演算法自動歸類結果分佈：")
        
        分佈 = df["風險嚴重度_SOI_Level"].value_counts().sort_index()
        for lvl, count in 分佈.items():
            # 計算該 Level 的平均指標，讓輸出更直觀
            群體篩選 = df[df["風險嚴重度_SOI_Level"] == lvl]
            平均值 = round(群體篩選[主要指標].mean(), 2)
            print(f"   🔹 {lvl} ：共 {count} 筆個案 (平均{主要指標}: {平均值})")
            
        print(f"📂 嚴重度特徵母表儲存路徑：{輸出路徑}")
        print("==================================================")
    except Exception as e:
        print(f"❌ 匯出集群母表失敗，原因: {e}")

if __name__ == "__main__":
    main()

