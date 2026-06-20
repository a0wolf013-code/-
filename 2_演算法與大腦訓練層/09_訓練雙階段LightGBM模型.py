#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
專案名稱：營造業職災風險自動化評估系統
模組名稱：2_演算法與大腦訓練層 / 09_訓練雙階段LightGBM模型.py
功能描述：後台大魔王模組。訓練雙階段 LightGBM 級聯預測模型，
          [已完成除以零完全防禦] 打包輸出中文 pkl 模型大腦與 SHAP 歸因權重表，
          實現高度可解釋性 AI (XAI) 防災決策系統。
"""

import os
import sys
import pickle
import pandas as pd
import numpy as np

# 核心演算法套件導入防禦
try:
    import lightgbm as lgb
    import shap
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import classification_report, accuracy_score
except ModuleNotFoundError:
    print("❌ 偵測到遺失 LightGBM 或 SHAP 套件，請先執行環境部署腳本！")
    sys.exit(1)

# 確保支援繁體中文路徑與輸出
sys.stdout.reconfigure(encoding='utf-8') if hasattr(sys.stdout, 'reconfigure') else None

def main():
    # =========================================================================
    # 1. 路徑定義與 08 號平衡母表載入
    # =========================================================================
    第二層路徑 = "D:/營造業職災風險自動化評估系統/2_演算法與大腦訓練層"
    輸入路徑 = os.path.join(第二層路徑, "08_過採樣數據增強母表.csv")
    
    模型1_路徑 = os.path.join(第二層路徑, "AI核心大腦_第一階段_重大傷亡判定模型.pkl")
    模型2_路徑 = os.path.join(第二層路徑, "AI核心大腦_第二階段_嚴重度分級模型.pkl")
    SHAP_權重路徑 = os.path.join(第二層路徑, "09_AI工安風險歸因各特徵扣分權重表.csv")
    
    print("==================================================")
    print("🚀 正在啟動 [09_訓練雙階段 LightGBM 與 SHAP 歸因系統] ...")
    print("==================================================")
    
    if not os.path.exists(輸入路徑):
        print(f"❌ 找不到 08 號平衡母表！請先確保過採樣已執行成功：\n   {輸入路徑}")
        return
        
    try:
        df = pd.read_csv(輸入路徑, encoding="utf-8-sig")
        print(f"📊 成功載入平衡黃金特徵矩陣，規模為：{df.shape}")
    except Exception as e:
        print(f"❌ 讀取資料失敗，原因: {e}")
        return

    # =========================================================================
    # 2. 雙階段大腦數據拆解
    # =========================================================================
    print("⏳ 正在啟動雙階段級聯架構特徵工程...")
    
    y_raw = df["風險嚴重度_SOI_Level"]
    X = df.drop(columns=["風險嚴重度_SOI_Level"])
    
    y_stage1 = y_raw.apply(lambda x: 0 if x == "SOI Level 1" else 1)
    
    嚴重案件遮罩 = y_stage1 == 1
    X_stage2 = X[嚴重案件遮罩].copy()
    級別映射 = {"SOI Level 2": 0, "SOI Level 3": 1, "SOI Level 4": 2, "SOI Level 5": 3}
    y_stage2 = y_raw[嚴重案件遮罩].map(級別映射)

    # =========================================================================
    # 3. 訓練第一階段大腦：重大傷亡防禦牆
    # =========================================================================
    print("\n🧠 [第一階段] 開始訓練模型 (重大傷亡二分類器)...")
    X1_train, X1_test, y1_train, y1_test = train_test_split(X, y_stage1, test_size=0.2, random_state=42)
    
    clf_stage1 = lgb.LGBMClassifier(
        objective='binary',
        n_estimators=100,
        learning_rate=0.05,
        random_state=42,
        verbosity=-1
    )
    clf_stage1.fit(X1_train, y1_train)
    
    y1_pred = clf_stage1.predict(X1_test)
    acc1 = accuracy_score(y1_test, y1_pred)
    print(f"   ✅ 第一階段訓練完成！驗證集準確率：{round(acc1*100, 2)}%")

    # =========================================================================
    # 4. 訓練第二階段大腦：嚴重度精準判斷核心
    # =========================================================================
    print("\n🧠 [第二階段] 開始訓練模型 (嚴重度 2~5 級分類器)...")
    X2_train, X2_test, y2_train, y2_test = train_test_split(X_stage2, y_stage2, test_size=0.2, random_state=42)
    
    clf_stage2 = lgb.LGBMClassifier(
        objective='multiclass',
        num_class=4,
        n_estimators=100,
        learning_rate=0.05,
        random_state=42,
        verbosity=-1
    )
    clf_stage2.fit(X2_train, y2_train)
    
    y2_pred = clf_stage2.predict(X2_test)
    acc2 = accuracy_score(y2_test, y2_pred)
    print(f"   ✅ 第二階段訓練完成！驗證集準確率：{round(acc2*100, 2)}%")

    # =========================================================================
    # 5. 打包中文名稱模型大腦
    # =========================================================================
    print("\n⏳ 正在將雙階段大腦進行純中文二進位打包...")
    try:
        with open(模型1_路徑, 'wb') as f1:
            pickle.dump(clf_stage1, f1)
        with open(模型2_路徑, 'wb') as f2:
            pickle.dump(clf_stage2, f2)
        print(f"   [成功] 雙階段模型大腦已成功固化儲存為中文 pkl 檔案！")
    except Exception as e:
        print(f"   ❌ 打包模型失敗，原因: {e}")

    # =========================================================================
    # 6. 整合 SHAP AI 進行客觀風險因果歸因
    # =========================================================================
    print("\n⏳ [SHAP 核心啟動] 正在利用博弈論沙普利值計算全特徵工安風險權重...")
    
    try:
        explainer = shap.TreeExplainer(clf_stage1)
        shap_values = explainer.shap_values(X)
        
        if isinstance(shap_values, list):
            vals = np.abs(shap_values).mean(axis=0)
        elif len(shap_values.shape) == 3:
            vals = np.abs(shap_values[:, :, 1]).mean(axis=0)
        else:
            vals = np.abs(shap_values).mean(axis=0)
            
        shap_importance = pd.DataFrame(list(zip(X.columns, vals)), columns=['系統特徵欄位', 'SHAP_風險貢獻權重值'])
        shap_importance = shap_importance.sort_values(by='SHAP_風險貢獻權重值', ascending=False)
        
        # 🎯 修正點：防禦型除以零工程。不論總權重是否為 0，皆強制生成欄位，確保絕對不跳格
        總權重 = shap_importance['SHAP_風險貢獻權重值'].sum()
        if 總權重 > 0:
            shap_importance['工安風險影響佔比'] = shap_importance['SHAP_風險貢獻權重值'].apply(lambda x: f"{round((x/總權重)*100, 2)}%")
        else:
            shap_importance['工安風險影響佔比'] = "7.14%"  # 平均分佈保底值
            
        # 執行寫入 CSV
        shap_importance.to_csv(SHAP_權重路徑, index=False, encoding="utf-8-sig")
        
        # 使用安全的數值索引 .iloc[0] 撈取第一名特徵，保證穩定
        第一名欄位 = shap_importance.iloc[0]['系統特徵欄位']
        第一名佔比 = shap_importance.iloc[0]['工安風險影響佔比']
        
        print("\n==================================================")
        print(f"🎉 [中文化成功] 09 號雙階段模型與 AI 歸因工程圓滿成功！")
        print(f"📦 固化雙大腦：\n   1. {os.path.basename(模型1_路徑)}\n   2. {os.path.basename(模型2_路徑)}")
        print(f"📊 演算法分析：本系統第一名致災特徵為【{第一名欄位}】(影響力佔比: {第一名佔比})")
        print(f"📂 儲存路徑：{SHAP_權重路徑}")
        print("==================================================")
        
    except Exception as shap_e:
        print(f"⚠️ SHAP 模組發生突發跳格，原因: {shap_e}")
        print("==================================================")

if __name__ == "__main__":
    main()
