#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
專案名稱：營造業職災風險自動化評估系統
模組名稱：3_智慧前端與應用層 / 10_施工網圖解析與語意對齊.py
功能描述：智慧前端核心。引入 Sentence-Transformers 語意向量模型，
          [內建自修復功能] 自動下載相容之繁體中文 NLP 引擎，
          將用戶輸入的 Excel 進度工序文字，與歷史職災核心特徵進行餘弦相似度對齊，
          將人類白話文自動轉譯為後台大腦認得的特徵向量。
"""

import os
import sys
import subprocess

# =========================================================================
# 0. 智慧型環境自修復核心 (防禦 Python 3.13 語意模型套件遺失與版本衝突)
# =========================================================================
try:
    from sentence_transformers import SentenceTransformer, util
except (ModuleNotFoundError, ImportError):
    print("⏳ [AI 語意引擎部署] 系統正在自動為您部署 Sentence-Transformers 自然語言核心...")
    print("   (此步驟大約需要 20-30 秒，系統會全自動處理，請放心等待...)")
    try:
        # 強制利用目前運行的執行緒，背景全自動拉取與 Python 3.13 完美互通的最新 NLP 相容包
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "sentence-transformers", "scikit-learn", "openpyxl"])
        print("🎉 [成功] AI 語意引擎部署完成！正在引導核心加載模型...")
        from sentence_transformers import SentenceTransformer, util
    except Exception as final_e:
        print(f"❌ 終極部署失敗，請嘗試手動重啟 Spyder 軟體。錯誤原因: {final_e}")
        sys.exit(1)

import pandas as pd
import numpy as np

# 確保支援繁體中文路徑與輸出
sys.stdout.reconfigure(encoding='utf-8') if hasattr(sys.stdout, 'reconfigure') else None

def main():
    # =========================================================================
    # 1. 路徑定義與資料夾防禦
    # =========================================================================
    第二層路徑 = "D:/營造業職災風險自動化評估系統/2_演算法與大腦訓練層"
    第三層路徑 = "D:/營造業職災風險自動化評估系統/3_智慧前端與應用層"
    
    # 輸入端：讀取 08 號特徵矩陣中的標準工種與缺失作為對齊基準
    特徵母表路徑 = os.path.join(第二層路徑, "08_過採樣數據增強母表.csv")
    輸出路徑 = os.path.join(第三層路徑, "10_施工網圖語意對齊結果矩陣.csv")
    
    print("==================================================")
    print("🚀 正在啟動 [10_施工網圖解析與語意對齊系統 (NLP)] ...")
    print("==================================================")
    
    if not os.path.exists(第三層路徑):
        os.makedirs(第三層路徑, exist_ok=True)

    # =========================================================================
    # 2. 智慧型檔案讀取策略 (Excel 自動偵測與模擬沙盒雙軌制)
    # =========================================================================
    # 尋找使用者放進第三層資料夾的施工進度表
    # 支援廠商常見的名字：進度表、工序、網圖、施工網圖等 Excel
    import glob
    excel_candidates = (
        glob.glob(os.path.join(第三層路徑, "*進度*.xlsx")) + 
        glob.glob(os.path.join(第三層路徑, "*工序*.xlsx")) +
        glob.glob(os.path.join(第三層路徑, "*網圖*.xlsx"))
    )
    
    廠商進度工序 = []
    
    if excel_candidates and os.path.exists(excel_candidates[0]):
        # 軌道一：使用者丟進來實體 Excel
        實體路徑 = excel_candidates[0]
        print(f"📂 [實體讀取] 偵測到用戶丟入施工進度表：{os.path.basename(實體路徑)}")
        try:
            df_excel = pd.read_excel(實體路徑)
            # 智慧過濾：自動找出包含「工序」、「項目」、「內容」或第一個文字欄位
            target_col = None
            for col in df_excel.columns:
                if any(k in str(col) for k in ["工序", "施工項目", "工作內容", "作業項目"]):
                    target_col = col
                    break
            if target_col is None:
                target_col = df_excel.select_dtypes(include=[object]).columns[0]
                
            廠商進度工序 = df_excel[target_col].dropna().astype(str).tolist()
            print(f"   ✅ 成功自實體 Excel (欄位: {target_col}) 中解析出 {len(廠商進度工序)} 項作業。")
        except Exception as ex_e:
            print(f"   ⚠️ 讀取實體 Excel 失敗({ex_e})，系統將自動切換為防禦型沙盒...")
            
    # 軌道二：防禦型模擬沙盒（若使用者還沒有丟 Excel，自動建立測試情境，保證全流程暢通）
    if not 廠商進度工序:
        print("💡 [提示] 未發現實體進度表 Excel，系統自動啟動【模擬施工網圖沙盒測試】...")
        廠商進度工序 = [
            "地下一樓連續壁擋土牆開挖與土方清運作業",
            "外部鋼管施工鷹架搭設作業與防墜安全網檢查",
            "高壓變電室活線接線與機電管線絕緣測試作業",
            "外牆水泥粉刷底層施作與油漆塗料防水粉刷"
        ]
        print(f"   [進度讀取] 模擬沙盒生成今日共 {len(廠商進度工序)} 項預定工序進行測試。")

    # =========================================================================
    # 3. 載入開源繁體中文高階語意模型大腦 (NLP Model Embedding)
    # =========================================================================
    print("\n⏳ 正在加載開源繁體中文多語系智慧語意模型 (paraphrase-multilingual)...")
    print("   (初次載入會自動從 HuggingFace 伺服器下載解碼器至本機，請維持網路暢通...)")
    try:
        # 使用開源且對繁體中文、多語黑話支持度極佳的輕量化頂級語意模型
        model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
        print("   [成功] AI 語意向量解碼大腦加載完畢！")
    except Exception as e:
        print(f"❌ 語意模型加載失敗，原因: {e}")
        return

    # =========================================================================
    # 4. 讀取系統標準致災特徵標籤庫
    # =========================================================================
    if not os.path.exists(特徵母表路徑):
        # 專家保底標準庫
        標準致災特徵標籤 = ["缺失_未配戴安全帶", "缺失_未設置護欄", "缺失_未設置防墜網", "缺失_未設置擋土支撐", "缺失_未斷電作業", "工種_模板工", "工種_鋼筋工", "工種_鷹架工", "工種_水電工", "工種_鐵工/鋼構工", "工種_泥水工", "特徵_當日降雨量(mm)", "特徵_最大瞬間風速(m/s)", "特徵_當日最高氣溫(°C)"]
    else:
        df_feat = pd.read_csv(特徵母表路徑, encoding="utf-8-sig")
        # 智慧抓取 08 號表裡所有的特徵（如缺失_、工種_、特徵_），作為對齊基準
        標準致災特徵標籤 = [str(col) for col in df_feat.columns if col.startswith("缺失_") or col.startswith("工種_") or col.startswith("特徵_")]
    
    print(f"⏳ 正在將 {len(標準致災特徵標籤)} 個系統標準致災特徵基因進行 AI 向量化編碼...")
    標準特徵向量庫 = model.encode(標準致災特徵標籤, convert_to_tensor=True)

    # =========================================================================
    # 5. 執行核心語意對齊工程：計算餘弦相似度 (Cosine Similarity Matching)
    # =========================================================================
    print("⏳ 智慧自然語言比對啟動：正在精準對齊廠商進度與歷史致災特徵基因...")
    
    對齊結果清單 = []
    
    for 工序 in 廠商進度工序:
        # A. 將用戶輸入的一行白話文，轉換為高維度 AI 語意向量
        工序向量 = model.encode(工序, convert_to_tensor=True)
        
        # B. 秒級計算這行白話文與系統所有標準致災欄位的「餘弦相似度（Cosine Similarity）」
        相似度分數矩陣 = util.cos_sim(工序向量, 標準特徵向量庫)
        
        # 將 Tensor 轉換為 numpy array 進行排序，拿到相似度最高的前兩名特徵索引
        相似度陣列 = 相似度分數矩陣.cpu().numpy()[0]
        前兩名索引 = np.argsort(相似度陣列)[::-1][:2]
        
        第一名索引 = 前兩名索引[0]
        第二名索引 = 前兩名索引[1]
        
        # C. 打包成語意對齊結果矩陣
        對齊行 = {
            "廠商進度預定工序": 工序,
            "AI語意自動對齊_第一核心特徵": 標準致災特徵標籤[第一名索引],
            "主特徵相似度信心度": f"{round(float(相似度陣列[第一名索引])*100, 2)}%",
            "AI語意自動對齊_第二核心特徵": 標準致災特徵標籤[第二名索引],
            "次特徵相似度信心度": f"{round(float(相似度陣列[第二名索引])*100, 2)}%"
        }
        對齊結果清單.append(對齊行)

    # =========================================================================
    # 6. 結構化橫向跨層級匯出對齊結果
    # =========================================================================
    df_output = pd.DataFrame(對齊結果清單)
    try:
        df_output.to_csv(輸出路徑, index=False, encoding="utf-8-sig")
        print("\n==================================================")
        print(f"🎉 [成功] 10 號施工網圖解析與語意對齊工程全面完工！")
        print(f"📊 智慧對齊成果：已成功將廠商白話文轉譯為模型系統可辨識之特徵基因")
        
        if not df_output.empty:
            print(f"🕵️‍♂️ 系統語意對齊範例：")
            範例 = df_output.iloc[0]
            print(f"   👉 廠商輸入白話工序：『{範例['廠商進度預定工序']}』")
            print(f"      🤖 AI 自動對齊 ➡️ 【{範例['AI語意自動對齊_第一核心特徵']}】(相似度: {範例['主特徵相似度信心度']})")
            
        print(f"📂 語意對齊結果矩陣儲存路徑：{輸出路徑}")
        print("==================================================")
    except Exception as e:
        print(f"❌ 匯出語意對齊矩陣失敗，原因: {e}")

if __name__ == "__main__":
    main()
