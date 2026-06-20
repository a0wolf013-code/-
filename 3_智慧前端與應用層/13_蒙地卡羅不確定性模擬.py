#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
專案名稱：營造業職災風險自動化評估系統
模組名稱：3_智慧前端與應用層 / 13_蒙地卡羅不確定性模擬.py
功能描述：不確定性風險量化引擎【全新 Plotly 互動繪圖版】。
          利用高效 Numpy 矩陣進行 10,000 次壓力測試，並透過 Plotly 引擎
          渲染出印刷級高解析度風險概率分佈圖（互動網頁版 HTML，支援滑鼠動態觀測與一鍵儲存 PNG）。
"""

import os
import sys
import pandas as pd
import numpy as np

# 🎯 核心防禦：改用完全不衝突的 Plotly 高階繪圖核心，消滅有毒的 matplotlib 報錯
try:
    import plotly.graph_objects as go
except ModuleNotFoundError:
    print("❌ 偵測到遺失 Plotly 套件，請先跑部署腳本進行安裝！")
    sys.exit(1)

# 確保支援繁體中文路徑與輸出
sys.stdout.reconfigure(encoding='utf-8') if hasattr(sys.stdout, 'reconfigure') else None

def 論文第四章_模擬風險總分公式(AI機率, 歷史裁罰, 水位, 安全係數, 缺失總數):
    """ 論文第四章核心風險加權公式 """
    法律風險分 = min(30, np.log1p(歷史裁罰) * 2.0)
    水位危險度 = max(0, 10 - abs(水位))
    安全係數不夠度 = max(0, (2.0 - 安全係數) * 20)
    地質風險分 = min(30, 水位危險度 + 安全係數不夠度)
    缺失風險分 = min(20, 缺失總數 * 3.0)
    AI預報分 = AI機率 * 20.0
    return min(100.0, max(0.0, 法律風險分 + 地質風險分 + 缺失風險分 + AI預報分))

def main():
    # =========================================================================
    # 1. 路徑定義與上游預警綜合表載入
    # =========================================================================
    第二層路徑 = "D:/營造業職災風險自動化評估系統/2_演算法與大腦訓練層"
    第三層路徑 = "D:/營造業職災風險自動化評估系統/3_智慧前端與應用層"
    
    輸入路徑 = os.path.join(第二層路徑, "12_全系統動態風險預警綜合評估表.csv")
    輸出表格路徑 = os.path.join(第三層路徑, "13_蒙地卡羅不確定性風險統計表.csv")
    輸出圖表路徑 = os.path.join(第三層路徑, "13_工地崩塌風險機率密度分佈圖.html")
    
    print("==================================================")
    print("🚀 正在啟動 [13_蒙地卡羅風險不確定性模擬系統 (Plotly 完全體)] ...")
    print("==================================================")
    
    if not os.path.exists(輸入路徑):
        print(f"❌ 核心阻斷：找不到 12 號綜合評估表！請確認 12 號腳本是否成功執行：\n   {輸入路徑}")
        return
        
    try:
        df_12 = pd.read_csv(輸入路徑, encoding="utf-8-sig")
        # 🎯 核心修正點：將 .iloc 改為 .iloc[0]，精準解鎖 Pandas 物件定位死鎖！
        標的工況 = df_12.iloc[0]
        print(f"📊 成功載入綜合評估表！系統自動鎖定最危險工況：【{標的工況['模擬工況編號']}】進行萬次壓力測試...")
    except Exception as e:
        print(f"❌ 讀取資料失敗，原因: {e}")
        return

    # =========================================================================
    # 2. 抽取與安全還原基底參數
    # =========================================================================
    AI機率base = float(str(標的工況["AI預測重大死傷機率"]).replace("%", "")) / 100.0
    歷史裁罰base = float(標的工況["特徵_歷史裁罰總額"])
    缺失總數base = int(標的工況["現場管理缺失總數"])
    水位base = float(標的工況["大地物理_地下水位(m)"] if "大地物理_地下水位(m)" in 標的工況 else -5.0)
    安全係數base = float(標的工況["大地物理_安全係數(FS)"] if "大地物理_安全係數(FS)" in 標的工況 else 1.5)
    
    # =========================================================================
    # 3. 執行 10,000 次蒙地卡羅不確定性隨機試驗
    # =========================================================================
    模擬次數 = 10000
    print(f"⏳ 機器學習矩陣運算啟動：正在執行 {模擬次數:,} 次隨機擾動疊代...")
    
    np.random.seed(42)
    
    AI機率_隨機矩陣 = np.clip(np.random.normal(loc=AI機率base, scale=0.08, size=模擬次數), 0.0, 1.0)
    水位_隨機矩陣 = np.random.normal(loc=水位base, scale=0.5, size=模擬次數)
    安全係數_隨機矩陣 = np.random.normal(loc=安全係數base, scale=0.1, size=模擬次數)
    缺失_隨機擾動 = np.random.choice([-1, 0, 1, 2], size=模擬次數, p=[0.2, 0.5, 0.2, 0.1])
    缺失_隨機矩陣 = np.maximum(0, 缺失總數base + 缺失_隨機擾動)
    
    蒙地卡羅分數結果 = np.array([
        論文第四章_模擬風險總分公式(
            AI機率_隨機矩陣[i], 歷史裁罰base, 水位_隨機矩陣[i], 安全係數_隨機矩陣[i], 缺失_隨機矩陣[i]
        ) for i in range(模擬次數)
    ])

    # =========================================================================
    # 4. 統計學指標計算與「實體致災概率 (%)」判定
    # =========================================================================
    print("⏳ 正在進行統計學不確定性收斂分析...")
    
    平均風險分數 = np.mean(蒙地卡羅分數結果)
    標準差風險 = np.std(蒙地卡羅分數結果)
    P50_中位數風險 = np.percentile(蒙地卡羅分數結果, 50)
    P95_極端高風險值 = np.percentile(蒙地卡羅分數結果, 95)
    
    紅燈臨界點 = 70.0
    超標次數 = np.sum(蒙地卡羅分數結果 >= 紅燈臨界點)
    實體崩塌致災機率 = (超標次數 / 模擬次數) * 100.0

    df_stat = pd.DataFrame({
        "統計指標名稱": ["模擬試驗總次數", "動態平均風險總分", "風險分佈標準差", "P50風險中位數", "P95極端高風險值", "臨界紅燈閥值(分)", "🚨 最終判定實體致災概率(%)"],
        "量化數值結果": [模擬次數, round(平均風險分數, 2), round(標準差風險, 2), round(P50_中位數風險, 2), round(P95_極端高風險值, 2), 紅燈臨界點, f"{round(實體崩塌致災機率, 2)}%"]
    })
    df_stat.to_csv(輸出表格路徑, index=False, encoding="utf-8-sig")

    # =========================================================================
    # 5. 數據視覺化：使用 Plotly 渲染高階工業級互動鐘形圖
    # =========================================================================
    print("⏳ 正在啟動 Plotly 智慧圖形渲染引擎，建立高學術價值互動式風險分佈圖...")
    
    try:
        # 使用 numpy 計算直方圖密度
        counts, bins = np.histogram(蒙地卡羅分數結果, bins=40, density=True)
        bin_centers = (bins[:-1] + bins[1:]) / 2
        
        fig = go.Figure()
        
        # 繪製常態風險分佈直方圖
        fig.add_trace(go.Bar(
            x=bin_centers, y=counts,
            name="蒙地卡羅試驗密度",
            marker_color='#34495e', opacity=0.6,
            hovertemplate="風險分數: %{x:.2f}分<br>機率密度: %{y:.4f}<extra></extra>"
        ))
        
        # 標記垂直指標線
        fig.add_vline(x=平均風險分數, line_dash="dash", line_color="#2980b9", line_width=2, 
                      annotation_text=f"平均分數: {round(平均風險分數,1)}分", annotation_position="top left")
        fig.add_vline(x=P95_極端高風險值, line_dash="dot", line_color="#e67e22", line_width=2, 
                      annotation_text=f"P95極端線: {round(P95_極端高風險值,1)}分", annotation_position="top right")
        fig.add_vline(x=紅燈臨界點, line_color="#c0392b", line_width=2.5, 
                      annotation_text=f"紅燈臨界牆: {紅燈臨界點}分", annotation_position="top right")
        
        # 美化排版設計
        fig.update_layout(
            title=f"<b>營造業工安風險不確定性量化分析 ── 蒙地卡羅模擬 ({模擬次數:,} 次試驗)</b>",
            title_font=dict(size=14),
            xaxis_title="系統自動化風險評估總分 (分)",
            yaxis_title="機率密度 (Probability Density)",
            template="plotly_white",
            hovermode="x unified",
            showlegend=True
        )
        
        # 🎯 核心成果導出：直接在第三層硬碟中噴出 HTML 網頁格式的黃金圖表！
        fig.write_html(輸出圖表路徑)
        
        print("\n==================================================")
        print(f"🎉 [大獲全勝] 13 號蒙地卡羅不確定性模擬工程成功封頂！")
        print(f"📊 試驗結論：在綜合 {模擬次數:,} 次環境與管理隨機震盪後")
        print(f"🧮 該極端危險工地 ── 最終判定實體致災概率為：【{round(實體崩塌致災機率, 2)} %】")
        print(f"🖼️  論文高階互動圖表已生成：{os.path.basename(輸出圖表路徑)}")
        print(f"💡 [操作指南] 請直接雙擊打開該 HTML 網頁，右上角按相機即可下載 300 DPI 論文用 PNG 圖！")
        print(f"📂 結構化數據表路徑：{輸出表格路徑}")
        print("==================================================")
    except Exception as e:
        print(f"❌ 渲染或輸出圖表失敗，原因: {e}")

if __name__ == "__main__":
    main()
