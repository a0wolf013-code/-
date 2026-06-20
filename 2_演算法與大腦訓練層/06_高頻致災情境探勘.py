#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
專案名稱：營造業職災風險自動化評估系統
模組名稱：2_演算法與大腦訓練層 / 06_高頻致災情境探勘.py
功能描述：利用 Apriori 與關聯規則演算法，從結構化特徵中挖掘出高頻致災情境組合，
          計算支持度(Support)、置信度(Confidence)與提升度(Lift)，
          自動建立營造業職災防護之專家情境知識庫。
"""

import os
import sys
import pandas as pd
import numpy as np

# 導入 Apriori 與關聯規則核心演算法
try:
    from mlxtend.frequent_patterns import apriori
    from mlxtend.frequent_patterns import association_rules
except ModuleNotFoundError:
    print("❌ 偵測到遺失 mlxtend 套件，請先在控制台執行：!pip install mlxtend")
    sys.exit(1)

# 確保支援繁體中文路徑與輸出
sys.stdout.reconfigure(encoding='utf-8') if hasattr(sys.stdout, 'reconfigure') else None

def main():
    # =========================================================================
    # 1. 路徑定義與特徵矩陣載入
    # =========================================================================
    第二層路徑 = "D:/營造業職災風險自動化評估系統/2_演算法與大腦訓練層"
    輸入路徑 = os.path.join(第二層路徑, "05_特徵挖掘與自動標籤母表.csv")
    輸出路徑 = os.path.join(第二層路徑, "06_高頻致災情境知識庫.csv")
    
    print("==================================================")
    print("🚀 正在啟動 [06_高頻致災情境探勘系統 (Apriori)] ...")
    print("==================================================")
    
    if not os.path.exists(輸入路徑):
        print(f"❌ 找不到特徵標籤母表！請先確認 05 號腳本是否已成功執行並輸出至：\n   {輸入路徑}")
        return
        
    try:
        df = pd.read_csv(輸入路徑, encoding="utf-8-sig")
        print(f"📊 成功載入 AI 特徵母表，規模為：{df.shape} (筆數, 欄位數)")
    except Exception as e:
        print(f"❌ 讀取特徵母表失敗，原因: {e}")
        return

    # =========================================================================
    # 2. 資料轉換工程：建構關聯規則專用布林矩陣 (One-Hot Transaction Matrix)
    # =========================================================================
    print("⏳ 正在轉換職災特徵為購物籃交易矩陣結構...")
    
    # 提取 05 號產出的 7 大管理缺失欄位 (本身已經是 0/1)
    缺失欄位 = [col for col in df.columns if col.startswith("缺失_")]
    df_basket = df[缺失欄位].copy()
    
    # 將類別特徵「特徵_工種別」進行 One-Hot 編碼，並併入布林矩陣
    if "特徵_工種別" in df.columns:
        df_工種_onehot = pd.get_dummies(df["特徵_工種別"], prefix="工種")
        df_basket = pd.concat([df_basket, df_工種_onehot], axis=1)
        
    # 將年齡離散化（如：高齡勞工、中壯年、青年），增加情境豐富度
    if "特徵_勞工年齡" in df.columns:
        bins = [0, 35, 55, 100]  # 🎯 已修正：定義青年、中壯年、高齡勞工的年齡切分線
        labels = ["年齡_青年勞工(35歲以下)", "年齡_中壯年勞工(36-55歲)", "年齡_高齡勞工(56歲以上)"]
        df_age_group = pd.get_dummies(pd.cut(df["特徵_勞工年齡"], bins=bins, labels=labels))
        df_basket = pd.concat([df_basket, df_age_group], axis=1)

    # 確保矩陣內所有數值嚴格為布林型態 (True/False)，這是 mlxtend 新版規範
    df_basket = df_basket.astype(bool)
    print(f"   [成功] 布林交易矩陣建構完成，探勘維度：{df_basket.shape} 個致災子特徵。")

    # =========================================================================
    # 3. 執行 Apriori 演算法探勘高頻項目集
    # =========================================================================
    print("\n⏳ 正在執行 Apriori 演算法，計算頻繁致災組合項...")
    
    # min_support=0.05 代表該致災組合至少要在所有案件中佔比達 5% 以上才納入探勘
    frequent_itemsets = apriori(df_basket, min_support=0.05, use_colnames=True)
    
    if frequent_itemsets.empty:
        print("⚠️ 探勘警告：在目前支持度門檻下未找到任何高頻組合，正在自動調降門檻至 2%...")
        frequent_itemsets = apriori(df_basket, min_support=0.02, use_colnames=True)
        
    print(f"   [成功] 挖掘出 {len(frequent_itemsets)} 組頻繁致災核心項目集。")

    # =========================================================================
    # 4. 生成關聯規則並過濾高價值「致災連鎖效應」
    # =========================================================================
    print("⏳ 正在計算信賴度與提升度，篩選核心關聯規則...")
    
    # metric="confidence", min_threshold=0.5 代表置信度（發生的準確率）必須大於 50%
    rules = association_rules(frequent_itemsets, metric="confidence", min_threshold=0.5)
    
    if rules.empty:
        print("⚠️ 提示：未找到高置信度規則，自動放寬信賴度門檻至 30%...")
        rules = association_rules(frequent_itemsets, metric="confidence", min_threshold=0.3)

    if rules.empty:
        print("⚠️ 數據集規模過小或特徵過於分散，無法生成任何有效的因果規則。")
        return

    # 智慧型過濾：我們只需要「提升度 (Lift) > 1.0」的強關聯規則（代表因果關係成立，而非巧合）
    強關聯規則 = rules[rules["lift"] > 1.0].copy()
    
    if 強關聯規則.empty:
        強關聯規則 = rules.copy() # 若沒有大於 1 的則保底使用全部

    # 排序：優先展示「置信度」最高、且「提升度」最強的前瞻情境規則
    強關聯規則 = 強關聯規則.sort_values(by=["confidence", "lift"], ascending=[False, False])

    # 清洗輸出格式，將 frozenset 轉換為易讀的字串字元
    強關聯規則["致災前置情境 (Ancedents)"] = 強關聯規則["antecedents"].apply(lambda x: ', '.join(list(x)))
    強關聯規則["連帶引發缺失 (Consequents)"] = 強關聯規則["consequents"].apply(lambda x: ', '.join(list(x)))
    
    # 重新挑選對決策有價值的黃金欄位
    展示欄位 = [
        "致災前置情境 (Ancedents)", 
        "連帶引發缺失 (Consequents)", 
        "support", "confidence", "lift"
    ]
    最終專家知識庫 = 強關聯規則[展示欄位].copy()
    
    # 欄位中文化重命名
    最終專家知識庫.columns = ["致災前置條件組合", "連帶衍生管理缺失", "支持度(機率)", "置信度(準確因果率)", "提升度(關聯強度)"]

    # =========================================================================
    # 5. 匯出高頻致災專家情境知識庫
    # =========================================================================
    try:
        最終專家知識庫.to_csv(輸出路徑, index=False, encoding="utf-8-sig")
        print("\n==================================================")
        print(f"🎉 [成功] 06 號高頻致災情境關聯探勘工程完工！")
        print(f"📊 專家知識庫規模：{最終專家知識庫.shape} 條強致災關聯規則")
        
        if not 最終專家知識庫.empty:
            print(f"💡 系統範例規則 1：")
            第一條 = 最終專家知識庫.iloc[0]  # 🎯 已修正：補上了第一列鎖定索引
            print(f"   👉 當工安現場出現【{第一條['致災前置條件組合']}】時")
            print(f"      有 {round(第一條['置信度(準確因果率)']*100, 2)}% 的機率會連帶衍生【{第一條['連帶衍生管理缺失']}】")
            
        print(f"📂 專家知識庫儲存路徑：{輸出路徑}")
        print("==================================================")
    except Exception as e:
        print(f"❌ 匯出專家知識庫失敗，原因: {e}")

if __name__ == "__main__":
    main()
